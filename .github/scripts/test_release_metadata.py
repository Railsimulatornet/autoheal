import subprocess
import unittest
from unittest.mock import patch
from release_metadata import REPOSITORY, make_metadata, remote_tag_exists


class MetadataTests(unittest.TestCase):
    def data(self, **kwargs):
        args = dict(version='1.0.1', event='push', ref='refs/heads/main', repository=REPOSITORY,
                    tag_exists=False, day='20260927', run='42', attempt='1')
        args.update(kwargs)
        return make_metadata(**args)

    def test_new_release(self):
        self.assertEqual(self.data()['tag'], '1.0.1')
        self.assertEqual(self.data()['release'], 'true')
        self.assertEqual(self.data()['publish'], 'true')

    def test_existing_release_gets_build_tag(self):
        d = self.data(tag_exists=True)
        self.assertEqual(d['tag'], '1.0.1-build.20260927.42.1')
        self.assertEqual(d['release'], 'false')

    def test_weekly_never_overwrites_release(self):
        self.assertEqual(self.data(event='schedule')['release'], 'false')
        self.assertEqual(self.data(event='schedule')['publish'], 'true')

    def test_manual_only_maintenance(self):
        self.assertEqual(self.data(event='workflow_dispatch')['release'], 'false')

    def test_pr_never_publishes(self):
        d = self.data(event='pull_request', ref='refs/pull/1/merge')
        self.assertEqual((d['release'], d['publish']), ('false', 'false'))

    def test_foreign_repository_never_publishes(self):
        self.assertEqual(self.data(repository='fixture/autoheal')['publish'], 'false')

    def test_feature_branch_never_publishes(self):
        self.assertEqual(self.data(ref='refs/heads/feature')['publish'], 'false')

    def test_matching_tag_release(self):
        self.assertEqual(self.data(ref='refs/tags/v1.0.1')['release'], 'true')

    def test_mismatched_tag_rejected(self):
        with self.assertRaises(ValueError):
            self.data(ref='refs/tags/v1.0.0')

    def test_invalid_values(self):
        for value in ('1.0', '01.0.1', '1.0.1-rc1', '1.0.1\nother=1'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.data(version=value)
        with self.assertRaises(ValueError):
            self.data(run='0')

    def test_retry_has_unique_name(self):
        self.assertNotEqual(self.data(tag_exists=True)['tag'], self.data(tag_exists=True, attempt='2')['tag'])

    @patch('release_metadata.subprocess.run')
    def test_lookup_errors_do_not_start_release(self, run):
        run.side_effect = subprocess.CalledProcessError(1, 'gh')
        with self.assertRaises(subprocess.CalledProcessError):
            remote_tag_exists('1.0.1')
        run.side_effect = None
        run.return_value.stdout = '[{"ref":"refs/tags/v1.0.10"}]'
        self.assertFalse(remote_tag_exists('1.0.1'))
        run.return_value.stdout = '[{"ref":"refs/tags/v1.0.1"}]'
        self.assertTrue(remote_tag_exists('1.0.1'))
        run.return_value.stdout = '{}'
        with self.assertRaises(ValueError):
            remote_tag_exists('1.0.1')


if __name__ == '__main__':
    unittest.main()
