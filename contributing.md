![Contributing Banner](media/contributing-banner.png)

# Guidelines

Please ensure your pull request adheres to the following guidelines:

- Search previous suggestions before making a new one, as yours may be a duplicate.
- Use the following format: `[App Name](link)`.
- New categories, or improvements to the existing categorization, are welcome.
- The pull request and commit should have an appropriate title.

## Minimum Criteria

An app must meet all of the following before it will be added:

- At least 50 stars on GitHub.
- The repository is at least 30 days old.
- At least one commit within the last 6 months (exceptions for offline players are acknowledged). Existing entries that fall out of activity for longer than this may be removed.
- Evidence the app actually works: a release, an APK, or a demo screenshot or GIF in the app's own README. Source code alone, with nothing showing it runs, is not sufficient.
- README must be written in English, or the primary README must link to an English translation.

## Forks

If the app is a fork of another project, including one already listed here, it should have a meaningful amount of the codebase changed: new features or a significant rework, not just a renamed package, a new icon, or a different color scheme.

Cosmetic-only forks will not be added, even if the original project is already listed.

Duplicate app names will not be added: check existing entries before submitting to avoid name collisions.

## Things That Will Draw Extra Scrutiny

Low-quality or low-effort repository submissions will not be added. This is judged at the maintainer's discretion.

## Adding Something to This List

1. Fork this repository.
2. Add your entry, in the correct section, in alphabetical order.
3. Check off each item in the checklist below within your pull request description.
4. Submit your pull request.

### Pull Request Checklist

```
- [ ] Entry is not a duplicate of an existing entry
- [ ] Repository has at least 30 stars
- [ ] Repository is at least 30 days old
- [ ] Repository has a commit within the last 6 months
- [ ] README of the repository is in English or has an English README linked in the primary README
- [ ] Repository has a release, APK, or binary, or a demo screenshot or GIF in its README
- [ ] Entry is added in the correct section, in alphabetical order
```

## Updating Your Pull Request

Sometimes a maintainer will ask you to edit your pull request before it is merged, most often because it did not fully meet the guidelines above.

## Removing or Flagging Existing Entries

If you notice an entry that no longer meets these criteria, whether abandoned, taken down, or if you would like your app removed from this list, or you believe an app has been listed without proper credit, license compliance, or for any other valid reason, please contact via [Email](mailto:rohithrpai07@proton.me)

## Automated application-link checks

Run these commands from the repository root with Python 3.10 or newer. No
additional packages or GitHub credentials are needed:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_links.py
python3 scripts/check_links.py --online
```

The checker covers the one-line list entries in Android Applications, iOS
Applications, Desktop Applications, Web Applications, and Resources. Keep each
entry in the existing `- [App Name](https://...)` format. Relative images,
contents links, and contact links outside these sections are not checked. This
is a deliberately narrow parser, not a general Markdown validator. If categories
or entry formatting change, update the checker and its tests in the same PR.

- **Errors** fail the check: non-HTTPS or malformed URLs, embedded credentials,
  backslashes/control characters, non-default ports, ambiguous hostnames,
  unsupported entry syntax, and GitHub links that are not repository roots.
- **Warnings** request human review: a missing/private repository, an archived
  repository, a redirect or changed repository identity, or an incomplete API
  check (for example, rate limits, timeouts, or an unexpected response).
- **Offline mode** validates syntax only. With `--online`, each distinct GitHub
  repository is checked once using public metadata from `api.github.com`.
  No other destination is fetched; redirects are never followed. Requests have
  timeouts and response-size limits and use neither credentials nor environment
  proxies. Unauthenticated API limits can leave some checks incomplete; the
  report explicitly labels these as warnings.

GitHub Actions runs tests and both modes for pull requests, pushes to `main`,
and manual runs. The workflow uses read-only permissions, a commit-pinned
checkout action with persisted credentials disabled, and no secrets. The report
is available in the workflow logs. First-time contributor workflows may require
maintainer approval before they run.

These checks do not audit application code, verify downloads, detect every
lookalike domain, or prove an app is safe. A working HTTPS link or unarchived
repository is not a security endorsement. Redirects and archived projects are
review signals, not proof of compromise. The workflow reports changes; it does
not automatically remove entries or post comments.
