#!/usr/bin/env python3
"""Validate the README's one-line application/resource entries (Python 3.10+)."""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

SECTIONS = {"Android Applications", "iOS Applications", "Desktop Applications",
            "Web Applications", "Resources"}
ENTRY = re.compile(r"[-*+] \[([^\[\]]+)\]\(([^\s()<>]+)\)")
REPOSITORY = re.compile(r"/([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+)/?")


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def entries(markdown):
    """Strictly require the project's documented inline format in list sections."""
    active = False
    seen_sections = set()
    links, findings = [], []
    for number, line in enumerate(markdown.splitlines(), 1):
        if line.startswith("## "):
            section = line[3:].strip()
            active = section in SECTIONS
            seen_sections.add(section)
        stripped = line.strip()
        if not active or not re.match(r"(?:[-*+]\s|\d+[.)]\s)", stripped):
            continue
        match = ENTRY.fullmatch(stripped)
        if not match:
            findings.append(("ERROR", number, "Use a single - [App Name](https://...) entry; reference, HTML, and multiline entries are unsupported."))
        else:
            links.append((number, match[2]))
    if not SECTIONS.issubset(seen_sections):
        findings.append(("ERROR", 1, "Expected README sections are missing; update the checker if categories change."))
    if not links:
        findings.append(("ERROR", 1, "No application/resource entries found."))
    return links, findings


def validate_url(url):
    """Return (error, optional owner/repo); never perform network I/O here."""
    if any(ord(c) <= 32 or ord(c) == 127 for c in url) or "\\" in url:
        return "Whitespace, control characters, and backslashes are forbidden.", None
    try:
        parts = urlsplit(url)
        port = parts.port
        host = parts.hostname
    except ValueError:
        return "Malformed URL or port.", None
    if parts.scheme.lower() != "https" or not host:
        return "Application/resource links must be absolute HTTPS URLs.", None
    if parts.username is not None or parts.password is not None:
        return "Embedded credentials/userinfo are forbidden (the text before @ is not the host).", None
    if not host.isascii() or "%" in parts.netloc:
        return "Use an explicit ASCII hostname without percent escapes.", None
    if port not in (None, 443):
        return "Only the default HTTPS port is allowed.", None
    if host != "github.com":
        return None, None
    match = REPOSITORY.fullmatch(parts.path)
    if not match or match[2] in {".", ".."} or parts.query or parts.fragment:
        return "GitHub entries must link directly to https://github.com/owner/repository.", None
    name = match[2].removesuffix(".git")
    if not name or name in {".", ".."}:
        return "Invalid GitHub repository name.", None
    return None, f"{match[1]}/{name}"


def repository_status(repository, opener):
    """GET a fixed GitHub API endpoint. No credentials, proxies, or redirects."""
    if not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", repository) or repository.split('/')[1] in {'.', '..'}:
        raise ValueError("Invalid repository identifier")
    request = Request(f"https://api.github.com/repos/{repository}", headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "music-app-directory-link-checker",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with opener.open(request, timeout=10) as response:
            body = response.read(1_000_001)
            if len(body) > 1_000_000:
                return "WARNING", "GitHub response too large; verification incomplete."
            data = json.loads(body)
        if not isinstance(data, dict) or not isinstance(data.get("full_name"), str) or not isinstance(data.get("archived"), bool):
            return "WARNING", "Unexpected GitHub response; verification incomplete."
        notes = []
        if data["full_name"].lower() != repository.lower():
            notes.append("Repository identity differs from the link; review ownership/name.")
        if data["archived"]:
            notes.append("Repository is archived; review maintenance status.")
        return ("WARNING", " ".join(notes)) if notes else ("OK", "Repository exists and is not archived.")
    except HTTPError as error:
        if error.code in (301, 302, 303, 307, 308):
            return "WARNING", "GitHub redirects this repository; review its owner/name. Redirect not followed."
        if error.code == 404:
            return "WARNING", "Repository is missing or not publicly accessible; review the link."
        return "WARNING", f"GitHub HTTP {error.code}; verification incomplete (possibly rate limited)."
    except (URLError, TimeoutError, OSError, ValueError) as error:
        return "WARNING", f"GitHub verification incomplete ({type(error).__name__})."


def check(markdown, online=False, opener=None):
    links, findings = entries(markdown)
    cache = {}
    if online and opener is None:
        opener = build_opener(ProxyHandler({}), NoRedirects())
    for line, url in links:
        error, repository = validate_url(url)
        if error:
            findings.append(("ERROR", line, error))
        elif online and repository:
            key = repository.lower()
            if key not in cache:
                cache[key] = repository_status(repository, opener)
            level, message = cache[key]
            if level != "OK":
                findings.append((level, line, message))
    return len(links), findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("readme", nargs="?", default="README.md")
    parser.add_argument("--online", action="store_true", help="Check deduplicated public repositories using only api.github.com")
    args = parser.parse_args(argv)
    try:
        markdown = Path(args.readme).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print(f"ERROR: Cannot read README ({type(error).__name__}).")
        return 1
    count, findings = check(markdown, args.online)
    for level, line, message in findings:
        print(f"{level} line {line}: {message}")
    errors = sum(level == "ERROR" for level, _, _ in findings)
    warnings = sum(level == "WARNING" for level, _, _ in findings)
    print(f"Checked {count} entries: {errors} error(s), {warnings} warning(s).")
    print("API checks enabled." if args.online else "Offline mode: repository availability was not checked.")
    print("These checks do not establish that an app or download is safe.")
    return int(errors > 0)


if __name__ == "__main__":
    sys.exit(main())
