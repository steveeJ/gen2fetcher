#!/usr/bin/env python

from setuptools import setup, find_packages  # Always prefer setuptools over distutils

name="gen2fetcher"

def get_version(relpath="__init__.py"):
    """read version info from file without importing it"""
    from os.path import dirname, join
    for line in open(join(dirname(__file__), name, relpath)):
        if '__version__' in line:
            if '"' in line:
                # __version__ = "0.9"
                return line.split('"')[1]
            elif "'" in line:
                return line.split("'")[1]

setup(
    name=name,
    description="A utility that allows downloading and verifying Gentoo stage3 and portage-snapshot archives.",
    version=get_version(),
    author="Stefan Junker",
    author_email="code@stefanjunker.de",
    packages=find_packages(),
    keywords="gentoo downloader stage3 portage",
    entry_points={
        'console_scripts': [
            'gen2fetcher=gen2fetcher:main'
        ]
    },
    install_requires=[
        'wget>2.2',
    ],
    classifiers=[
        'Environment :: Console',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Gentoo :: Download :: Utilities',
    ],
)
