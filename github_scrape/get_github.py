#!/usr/bin/env python
import tarfile
from github import Github
from git import Repo
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

def clone_and_archive(repo_name, url, time, destination: Path, meta=[], wiki_url=''):
    output_to = destination/'{repo}_github_archive_{time}.tar.gz'.format(repo=repo_name, time=time)
    archive_name = '{repo}_{time}'.format(repo=repo_name, time=time)
    clone_to = destination/'{repo}_repo_archive'.format(repo=repo_name)
    Repo.clone_from(url, clone_to)
    if wiki_url:
        wiki_to = '{repo}_wiki_{time}'.format(repo=repo_name, time=time)
        Repo.clone_from(wiki_url, wiki_to)

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
    wiki_url = ''
    if repo.has_wiki:
        #Remove .git from clone_url, append .wiki.git to get wiki repo
        wiki_url = repo.clone_url[:-3]+'wiki.git'

    #finally get the repo code itself
    clone_url = repo.clone_url
    archive_name = clone_and_archive(repo_name, clone_url, time, destination, meta, wiki_url)
    print("Repo {} archived at {}".format(repo_name, archive_name))
