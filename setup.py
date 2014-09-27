#!/usr/bin/env python

from setuptools import setup, find_packages # Always prefer setuptools over distutils
from codecs import open # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name = "gen2fetcher",
    description="A utility that allows downloading and verifying Gentoo stage3 and portage-snapshot archives.",
    version = "0.1",
    author = "Stefan Junker",
    author_email = "code@stefanjunker.de",
    packages=find_packages(),
    keywords="gentoo downloader stage3 portage",
    entry_points={
        'console_scripts': [
            'gen2fetcher=gen2fetcher:main',
        ],
    },
)