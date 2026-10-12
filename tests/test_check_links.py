import io
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError, URLError
from urllib.request import Request
from scripts.check_links import NoRedirects, check, entries, repository_status, validate_url


def readme(*urls):
    return ('## Android Applications\n' + ''.join(f'- [App]({url})\n' for url in urls)
            + '## iOS Applications\n## Desktop Applications\n## Web Applications\n## Resources\n')


def response(payload):
    result = Mock()
    result.__enter__ = Mock(return_value=io.BytesIO(payload))
    result.__exit__ = Mock(return_value=False)
    return result


class LinkTests(unittest.TestCase):
    def test_valid_repository(self):
        for url in ('https://github.com/owner/repo', 'https://GITHUB.com/owner/repo/', 'https://github.com/owner/repo.git'):
            self.assertEqual(validate_url(url), (None, 'owner/repo'))

    def test_deceptive_and_malformed_urls(self):
        for url in ('http://github.com/a/b', '//github.com/a/b', 'javascript:alert(1)',
                    'https://github.com@evil.example/a', 'https://user:pass@github.com/a/b',
                    'https://github.com\\@evil.example/a', 'https://github.com/a/../b',
                    'https://github.com/a/%2e%2e', 'https://github.com/a/b?x=y',
                    'https://github.com/a/b#x', 'https://github.com/a/b/releases',
                    'https://github.com:bad/a/b', 'https://github.com:80/a/b',
                    'https://github.com/a/..', 'https://github.com/a/.git',
                    'https://git%68ub.com/a/b', 'https://gıthub.com/a/b',
                    'https://github.com/\na/b', 'https://[broken'):
            with self.subTest(url=url):
                self.assertIsNotNone(validate_url(url)[0])

    def test_non_github_never_fetched(self):
        opener = Mock()
        count, findings = check(readme('https://example.com', 'https://github.com.evil.example/a/b', 'https://127.0.0.1/'), True, opener)
        self.assertEqual((count, findings), (3, []))
        opener.open.assert_not_called()

    def test_invalid_urls_never_fetched(self):
        opener = Mock()
        _, findings = check(readme('https://github.com@evil.example/a'), True, opener)
        self.assertEqual(findings[0][0], 'ERROR')
        opener.open.assert_not_called()

    def test_offline_never_fetched(self):
        opener = Mock()
        check(readme('https://github.com/a/b'), False, opener)
        opener.open.assert_not_called()

    def test_duplicate_repositories_checked_once(self):
        opener = Mock()
        opener.open.return_value = response(b'{"full_name":"a/b","archived":false}')
        self.assertEqual(check(readme('https://github.com/a/b', 'https://github.com/A/B/'), True, opener), (2, []))
        opener.open.assert_called_once()
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.github.com/repos/a/b')
        self.assertIsNone(request.get_header('Authorization'))
        self.assertEqual(opener.open.call_args.kwargs['timeout'], 10)

    def test_archived_and_identity_change(self):
        opener = Mock()
        opener.open.return_value = response(b'{"full_name":"new/b","archived":true}')
        level, message = repository_status('a/b', opener)
        self.assertEqual(level, 'WARNING')
        self.assertIn('identity', message)
        self.assertIn('archived', message)

    def test_http_failures_are_review_warnings(self):
        for status in (301, 302, 307, 308, 404, 403, 429, 500):
            opener = Mock()
            opener.open.side_effect = HTTPError('https://api.github.com/repos/a/b', status, '', {}, None)
            self.assertEqual(repository_status('a/b', opener)[0], 'WARNING')
            opener.open.assert_called_once()

    def test_invalid_responses(self):
        for payload in (b'not JSON', b'[]', b'{}', b'{"full_name":"a/b","archived":"false"}', b'x' * 1_000_001):
            opener = Mock()
            opener.open.return_value = response(payload)
            self.assertEqual(repository_status('a/b', opener)[0], 'WARNING')

    def test_network_errors(self):
        for error in (URLError('offline'), TimeoutError()):
            opener = Mock()
            opener.open.side_effect = error
            self.assertEqual(repository_status('a/b', opener)[0], 'WARNING')

    def test_redirect_handler_refuses_all_destinations(self):
        for target in ('http://127.0.0.1', 'https://evil.example', 'https://api.github.com/repositories/1'):
            self.assertIsNone(NoRedirects().redirect_request(Request('https://api.github.com/repos/a/b'), None, 301, '', {}, target))

    def test_strict_entry_format(self):
        for entry in ('- [App][ref]', '- <a href="https://example.com">App</a>', '- [App](https://example.com) extra', '1. [App](https://example.com)', '- [App](\nhttps://example.com)'):
            _, findings = entries(readme().replace('## Android Applications\n', '## Android Applications\n' + entry + '\n'))
            self.assertTrue(any(level == 'ERROR' for level, _, _ in findings))

    def test_missing_sections_or_empty_document_fail(self):
        for markdown in ('', '## Other\n- [App](https://example.com)', readme()):
            self.assertTrue(entries(markdown)[1])

    def test_relative_images_and_contents_are_out_of_scope(self):
        markdown = '![Banner](media/banner.png)\n## Contents\n- [Apps](#android-applications)\n' + readme('https://github.com/a/b')
        self.assertEqual(check(markdown), (1, []))

    def test_repository_identifier_cannot_escape_api_path(self):
        for repository in ('../a', 'a/..', 'a/b?x=1', 'a/b/c', 'a%2fb/c'):
            with self.assertRaises(ValueError):
                repository_status(repository, Mock())


if __name__ == '__main__':
    unittest.main()
