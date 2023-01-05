#!/usr/bin/env python
import tarfile
#Rate limit retries provided by GithubRetry are currently only available from this PR branch
#https://github.com/PyGithub/PyGithub/pull/2387
#so to use this, that branch needs to be pulled and pygithub installed from there.
from github import Github, GithubRetry
from git import Repo, exc
import json
import requests
from time import strftime, gmtime
import os
import shutil
from pathlib import Path
from functools import partial
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from github import Repository

_repo_types = ['public', 'private', 'all']

def dump_list(repo_name, time, destination: Path, output_name, obj):
    output_file = destination/"{repo}_{name}_{time}.json".format(repo=repo_name, name=output_name, time=time)

    with open(output_file, 'w') as outfile:
        outfile.write("{{ {name} = [\n".format(name=output_name))
        for item in obj:
            #json.dump(item, outfile)
            json.dump(item.raw_data, outfile)
            outfile.write(',\n')
        outfile.seek(outfile.tell() - 2, os.SEEK_SET)
        outfile.truncate()
        outfile.write("\n]\n}\n")
    return output_file

def download_archive(repo_name, link):
    output_to = "{repo}_archive.tar.gz".format(repo=repo_name)
    with requests.get(link, stream=True) as req:
        req.raise_for_status()
        with open(output_to , "wb") as outfile:
            for chunk in req.iter_content(chunk_size=8192):
                if chunk:
                    outfile.write(chunk)
    return output_to

def clone_and_archive(repo_name, url, time, destination: Path, meta=[], wiki_url=''):
    output_to = destination/'{repo}_github_archive_{time}.tar.gz'.format(repo=repo_name, time=time)
    archive_name = '{repo}_{time}'.format(repo=repo_name, time=time)
    clone_to = destination/'{repo}_repo_archive'.format(repo=repo_name)
    Repo.clone_from(url, clone_to)
    if wiki_url:
        wiki_to = '{repo}_wiki_{time}'.format(repo=repo_name, time=time)
        try:
             Repo.clone_from(wiki_url, wiki_to)
        except exc.GitCommandError as error:
            print(f"Not archiving wiki repo for {url}.  It likely doesn't exist, or doesn't have public permissions.")
            wiki_url = '' #Unset the url if it failed to clone so we don't archive it next...

    with tarfile.open(output_to, mode='w:gz') as tf:
        tf.add(clone_to, arcname='{}/repo/{}'.format(archive_name, clone_to))
        for f in meta:
            tf.add(f, arcname='{}/meta/{}'.format(archive_name, f))
            os.remove(f)
        if wiki_url:
            tf.add(wiki_to, arcname='{}/wiki/{}'.format(archive_name, wiki_to))

    shutil.rmtree(clone_to)
    if wiki_url:
        shutil.rmtree(wiki_to)

    return output_to

def get_repo_meta(repo: 'Repository', time: str, destination: Path) -> Iterable[str]:
    """
        Query the Github api for repository metadata info, includes
        comments, issues, issue comments, pull requests, pull request comments, code review comments

        Parameters
        ----------
            repo   a Github.Repository object to retrieve meatadata for
            time   timestamp to append to output files
            destination Path to destination dirctory where serialized metadata will be written to
        Returns
        -------
            list of file names which contain the serialized meta data for each of the supported types (in json format)
    """
    #Hold a list of all metadata to dump for archving
    meta = []
    repo_name = repo.full_name.split('/')[-1]
    dump = partial(dump_list, repo_name, time, destination)
    #get all comments for repo
    comments = repo.get_comments()
    meta.append( dump("comments", comments) )

    #get all issues
    issues = repo.get_issues(state="all")
    meta.append( dump("issues", issues) )

    #Get all comments on issues
    issue_comments = repo.get_issues_comments()
    meta.append( dump("issue_comments", issue_comments) )

    #Get pull requests
    pulls = repo.get_pulls(state="all")
    meta.append( dump("pulls", pulls) )

    #Get pull request comments (conversation)
    pull_comments = repo.get_pulls_comments()
    meta.append( dump("pulls_comments", pull_comments) )

    #Get all code review comments for PRs
    pull_review_comments = repo.get_pulls_review_comments()
    meta.append( dump("pulls_review_comments", pull_review_comments) )

    #If used, get project info
    #if repo.has_projects:
        #projects = repo.get_projects()

    #If release artififacts exist
    #releases = repo.get_releases()
    return meta

def archive_repo(repo: 'Repository', time: str, destination: Path):
    """
        Pull all relevant metadata about repository, clone the repository, and
        archive the information in a tar.gz archive suffixed with the time provided.

        Parameters
        ----------
        repo        github Repository object to archive
        time        timestamp to append to output files
        destination Path to the output location to store the archive.
    """

    meta = get_repo_meta(repo, time, destination)
    repo_name = repo.full_name.split('/')[-1]
    wiki_url = ''
    if repo.has_wiki:
        #Note this just tells us whether the wiki is enabled for the repo
        #but it appears that if no content has been added to the wiki, the git repo isn't created
        #hence this url may be invalid. Should treat is as potentialy non-existent.
        #Remove .git from clone_url, append .wiki.git to get wiki repo
        wiki_url = repo.clone_url[:-3]+'wiki.git'
    #finally get the repo code itself
    clone_url = repo.clone_url
    archive_name = clone_and_archive(repo_name, clone_url, time, destination, meta, wiki_url)
    print("Repo {} archived at {}".format(repo_name, archive_name))

def archive_org_repos(organization: str, api_token: str, destination: Path, type: str = 'public', skip: Iterable[str] = [], only: Iterable[str] = []):
    """
        Find all repositories in the given organization and use the api_token to scrape repo data

        Parameters
        ----------
        organization    str containing the organization name, i.e. NOAA-OWP

        api_token       API token with approriate access permissions for the requested type of repos to archive

        destination     Path to the output location to store the archive.

        type            the type of repositories to archive, may be 'all', 'public', 'private'

        skip            list of repositories to skip
        only            list of repositories to archive

	skip and only are mutually exclusive arguements.  If skip is not empty, only must be.  If only is not empy, skip must be.
    """

    if skip and only:
        raise( ValueError("skip and only are both non-empty, only one can be applied.") )

    if type not in _repo_types:
        raise ValueError("Unsupported repo type: {}. Valid options are {}".format(type, _repo_types))
    #Timestamp to build output files
    time = strftime("%Y-%m-%d_%H:%M:%S", gmtime())
    #Connect to the github organization
    gh = Github(api_token, retry=GithubRetry(total=11))
    org = gh.get_organization(organization)

    #TODO check that this is limited to only PUBLIC repositories, or at least flexible enough to differentiate
    #Make funcitons with public/private/all option, verify repo status, make input param
    
    for repo in org.get_repos():
        name = repo.full_name.split('/')[-1]
        if skip and name in skip:
            print(f'Skipping repo {name}...')
            continue
        elif not only or name in only:
            #We either are skipping specific repos, in which case we get here by `not only`.
            #Or we are only processing certain repos, in which case get here by `name in only`.
            #If we are doing neither of those, then both are True and we process all repos
            print(f'Processing repo {name}')
            print("    current API rate limit: {}".format(gh.get_rate_limit().core) )
            if type == 'all':
                #Archive all repos, regardless of status
                archive_repo(repo, time, destination)
            elif not repo.private and type == 'public':
                #only archive public repositories
                archive_repo(repo, time, destination)
            elif repo.private and type == 'private':
                #only archive private repositories
                archive_repo(repo, time, destination)
            else:
                continue

if __name__ == "__main__":
    raise RuntimeError('Module {} called directly; use main package entrypoint instead')
