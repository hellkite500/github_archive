#!/usr/bin/env python3
'''github_scrape setup file'''

from setuptools import setup, find_packages
from os.path import abspath, dirname, join
from io import open

root_dir = abspath(dirname(__file__))

short_description = '''A utility for archiving GitHub repositories along with development
metadata, including issues, comments, and code review comments'''

# Use README.md as long description
with open(join(root_dir, 'README.md'), mode='r') as f:
    long_description = f.read()

#Load version info
exec(open('github_scrape/_version.py').read())

setup(
    # Package version and information
    name='github_scrape',
    version=__version__,
    packages=find_packages(exclude=['*test*']),
    url='https://github.com/hellkite500/github_scrape',

    # Set entry point for CLI
    entry_points= {
        'console_scripts' : ['github_scrape=github_scrape.__main__:main'],
        },

    # Package description information
    description=short_description
    long_description_content_type='text/markdown',

    # Author information
    author='Nels Frazier',
    author_email='',

    license='CC 0',

    # Search keywords
    keywords='github archive backup',
    python_requires='>=3.5',
    install_requires=[
        'pyyaml',
        'pygithub',
        'gitpython',
    ],
)
