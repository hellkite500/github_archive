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
