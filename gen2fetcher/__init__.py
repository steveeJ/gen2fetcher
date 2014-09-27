#!/usr/bin/env python2

from __future__ import print_function
import datetime, wget, os
from string import Template
import hashlib
import argparse


class Downloader():
    """
    Base Class which serves as a partial implementation to common methods.
    """
    def __init__(self, date, arch, directory, overwrite=False):
        self.date = date
        self.arch = arch
        self.directory = directory
        self.overwrite = overwrite

    @property
    def BASE_URL(self):
        raise NotImplementedError("Class %s doesn't implement this method" % (self.__class__.__name__))

    @property
    def FILENAME(self):
        raise NotImplementedError("Class %s doesn't implement this method" % (self.__class__.__name__))

    @property
    def CONTENTS_SUFFIX(self):
        raise NotImplementedError("Class %s doesn't implement this method" % (self.__class__.__name__))

    @property
    def CHECKSUM_SUFFIX(self):
        raise NotImplementedError("Class %s doesn't implement this method" % (self.__class__.__name__))

    @property
    def base_url(self):
        return self.BASE_URL.substitute(date=self.date, arch=self.arch)

    @property
    def filename(self):
        return self.FILENAME.substitute(date=self.date, arch=self.arch)

    @property
    def _target_file(self):
        return "%s/%s" % (self.directory, self.filename)

    @property
    def _checkum_file(self):
        return "%s/%s%s" % (self.directory, self.filename, self.CHECKSUM_SUFFIX)

    def _verify(self):
        raise NotImplementedError("Class %s doesn't implement this method" % (self.__class__.__name__))

    def _clean(self):
        for filepath in [self._target_file, self._checkum_file]:
            if os.path.exists(filepath):
                print("INFO: Renaming %s" % filepath)
                os.rename(filepath, "%s.old" % filepath)

    def _download(self):
        if os.path.exists(self._target_file):
            if self.overwrite:
                print("DEBUG: Chose to overwrite old files.")
                self._clean()
            elif not self.verify():
                print("WARNING: Previous download seems corrupted.")
                self._clean()
            else:
                print("INFO: Using previously downloaded %s" % self.filename)
                return self.filename
        elif not os.path.exists(self.directory):
            print("INFO: Creating %s" % self.directory)
            os.mkdir(self.directory)

        try:
            for filename in [self.filename, self.filename + self.CHECKSUM_SUFFIX]:
                print("INFO: Downloading %s" % filename)
                wget.download(self.base_url + filename, out=self.directory, bar=wget.bar_thermometer)
                print("")
            if self.verify():
                return self._target_file
            else:
                return None
        except Exception as e:
            print("ERROR: Failed to download %s\n%s" % (filename, e.message))

    def download(self):
        if self.date is None:
            print("DEBUG: Assuming today for archive date")
            self.date = datetime.datetime.today().strftime("%Y%m%d")

        day = datetime.datetime.strptime(self.date, "%Y%m%d")
        filename = None
        for i in list(range(6)):
            day -= datetime.timedelta(days=1)
            self.date = day.strftime("%Y%m%d")
            filename = self._download()
            if filename is not None:
                break
        return filename

    def verify(self):
        result = False
        print("INFO: Checksum verification of %s: " % self.filename, end="")
        try:
            result = self._verify()
            if result:
                print(":-)")
            else:
                print(":-(")
        except Exception as e:
            print(":-(")
            print("ERROR: %s" % e)
        return result

class Stage3Downloader(Downloader):
    @property
    def BASE_URL(self):
        return Template("http://distfiles.gentoo.org/releases/$arch/autobuilds/$date/")

    @property
    def FILENAME(self):
        return Template("stage3-$arch-$date.tar.bz2")

    @property
    def CHECKSUM_SUFFIX(self):
        return ".DIGESTS"

    def _verify(self):
        BLOCKSIZE = 65536
        hasher = hashlib.sha512()
        with open(self._target_file, "rb") as targetfile:
            buf = targetfile.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = targetfile.read(BLOCKSIZE)

        with open(self._checkum_file, "rb") as digestfile:
            expected = ""
            lastchar = ""
            digestfile.readline()
            while (lastchar != " "):
                expected += lastchar
                lastchar = digestfile.read(1)
            return expected == hasher.hexdigest()


class PortageDownloader(Downloader):
    @property
    def BASE_URL(self):
        return Template("http://distfiles.gentoo.org/releases/snapshots/current/")

    @property
    def FILENAME(self):
        return Template("portage-$date.tar.xz")

    @property
    def CHECKSUM_SUFFIX(self):
        return ".md5sum"

    def _verify(self):
        hasher = hashlib.md5()
        with open(self._target_file, "rb") as targetfile:
            buf = targetfile.read()
            hasher.update(buf)

        with open(self._checkum_file, "rb") as md5file:
            expected = ""
            lastchar = ""
            while (lastchar != " "):
                expected += lastchar
                lastchar = md5file.read(1)
            return expected == hasher.hexdigest()

def download(args):
    if args.stage3:
        stage3_downloader = Stage3Downloader(args.date, args.arch, args.directory, args.overwrite)
        stage3_downloader.download()

    if args.portage:
        portage_downloader = PortageDownloader(args.date, args.arch, args.directory, args.overwrite)
        portage_downloader.download()

def verify(args):
    if args.stage3:
        stage3_downloader = Stage3Downloader(args.date, args.arch, args.directory)
        stage3_downloader.verify()

    if args.portage:
        portage_downloader = PortageDownloader(args.date, args.arch, args.directory)
        portage_downloader.verify()

def main():
    parser = argparse.ArgumentParser(description="Utility for retrieving Gentoo stage3+portage archives")
    parser.add_argument("--arch", nargs="?", default="amd64", help="ARCH for stage3 archive")
    parser.add_argument("--stage3", action="store_true", default=False, help="Process stage3 archive")
    parser.add_argument("--portage", action="store_true", default=False, help="Process portage snapshot")
    parser.add_argument("--directory", nargs="?", default="download/")

    # Subparser action
    subparsers = parser.add_subparsers(dest='action')
    subparsers.required = True
    ## download
    parser_download = subparsers.add_parser('download')
    parser_download.add_argument("--date", required=False, default=None, help="Request a specific archive date.")
    parser_download.add_argument("-o", "--overwrite", action="store_true", default=False)
    parser_download.set_defaults(func=download)
    ## verify
    parser_verify = subparsers.add_parser('verify')
    parser_verify.add_argument("--date", required=True, help="Request a specific archive date.")
    parser_verify.set_defaults(func=verify)

    args = parser.parse_args()
    args.func(args)