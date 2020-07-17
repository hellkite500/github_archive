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

