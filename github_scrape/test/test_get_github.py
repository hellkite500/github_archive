import unittest
from pathlib import Path
from time import strftime, gmtime
from github import Github
from .. import get_repo_meta, clone_and_archive

class TestGetGithub(unittest.TestCase):
    """
        Test coverage for the get_github module
    """
    _current_dir = Path(__file__).resolve().parent

    def setUp(self):
        self.token = ''
        if self.token:
            #Token auth github, higher rate limit
            self.github = Github(self.token)
        else:
            #Anonimous github, severly rate limited API
            self.github = Github()
        self.org_string = 'NOAA-OWP'
        self.repo_string = 'owp-open-source-project-template'
        self.repo_w_wiki = 'DMOD'
        self.org = self.github.get_organization(self.org_string)
        self.wiki_repo = self.org.get_repo(self.repo_w_wiki)
        self.repo = self.org.get_repo(self.repo_string)
        self.time = strftime("%Y-%m-%d_%H:%M:%S", gmtime())

    def tearDown(self):
        for p in Path(TestGetGithub._current_dir).glob("*.json"):
            if p.is_file():
                p.unlink()
        for p in Path(TestGetGithub._current_dir).glob("*.tar.gz"):
            if p.is_file():
                p.unlink()

    def test_get_repo_meta(self):
        """
            Test the archive_repo function to ensure all meta data is properly captured
        """
        meta = get_repo_meta(self.repo, self.time, TestGetGithub._current_dir)
        self.assertIsNotNone(meta)
        self.assertTrue(len(meta), 6)
        #defer name substitution
        pattern =  "{repo}_{name}_{time}.json".format(repo=self.repo_string, name="{name}", time=self.time)
        self.assertEqual(meta[0].name, pattern.format(name='comments'))
        self.assertEqual(meta[1].name, pattern.format(name='issues'))
        self.assertEqual(meta[2].name, pattern.format(name='issue_comments'))
        self.assertEqual(meta[3].name, pattern.format(name='pulls'))
        self.assertEqual(meta[4].name, pattern.format(name='pulls_comments'))
        self.assertEqual(meta[5].name, pattern.format(name='pulls_review_comments'))

        self.assertTrue((TestGetGithub._current_dir/pattern.format(name='comments')).exists())
        self.assertTrue((TestGetGithub._current_dir/pattern.format(name='issues')).exists())
        self.assertTrue((TestGetGithub._current_dir/pattern.format(name='issue_comments')).exists())
        self.assertTrue((TestGetGithub._current_dir/pattern.format(name='pulls')).exists())
        self.assertTrue((TestGetGithub._current_dir/pattern.format(name='pulls_comments')).exists())
        self.assertTrue((TestGetGithub._current_dir/pattern.format(name='pulls_review_comments')).exists())

