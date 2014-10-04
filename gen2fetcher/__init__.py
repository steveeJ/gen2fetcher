#!/usr/bin/env python

from __future__ import print_function
import datetime, wget, os
from string import Template
import hashlib
import argparse
import logging as log

__version__ = "0.1.4"

def get_loglevel(verbosity, minimum=3):
    VERBOSITY_LOGLEVEL = { 0: log.CRITICAL,
                           1: log.ERROR,
                           2: log.WARNING,
                           3: log.INFO,
                           4: log.DEBUG }
    verbosity += minimum
    if verbosity > list(VERBOSITY_LOGLEVEL.keys())[-1]:
        return list(VERBOSITY_LOGLEVEL.keys())[-1]
    else:
        return VERBOSITY_LOGLEVEL[verbosity]


class Downloader():
    """
    Base Class which serves as a partial implementation to common methods.
    """
    def __init__(self, date, arch, directory, overwrite=False, subarch=None, history=7):
        """

        :param date: Date to be specified in YYYYMMDD format
        :param arch: ARCH for the stage3 image
        :param directory: Target directories for downloaded/verified files
        :param overwrite: Specifies if a re-download should be forced even if files are in-place
        """
        self.date = date
        self.arch = arch
        if subarch is None:
            subarch = arch
        self.subarch = subarch
        self.directory = directory
        self.overwrite = overwrite
        self.history = history

    @property
    def BASE_URL(self):
        raise NotImplementedError("Class %s doesn't implement this method" % self.__class__.__name__)

    @property
    def FILENAME(self):
        raise NotImplementedError("Class %s doesn't implement this method" % self.__class__.__name__)

    @property
    def CONTENTS_SUFFIX(self):
        raise NotImplementedError("Class %s doesn't implement this method" % self.__class__.__name__)

    @property
    def CHECKSUM_SUFFIX(self):
        raise NotImplementedError("Class %s doesn't implement this method" % self.__class__.__name__)

    @property
    def base_url(self):
        return self.BASE_URL.substitute(date=self.date, arch=self.arch)

    @property
    def filename(self):
        return self.FILENAME.substitute(date=self.date, subarch=self.subarch)

    @property
    def _target_file(self):
        return "%s/%s" % (self.directory, self.filename)

    @property
    def _checkum_file(self):
        return "%s/%s%s" % (self.directory, self.filename, self.CHECKSUM_SUFFIX)

    @property
    def CHECKSUM_KEYWORD(self):
        raise NotImplementedError("Class %s doesn't implement this method" % self.__class__.__name__)

    def _verify_hasher(self):
        raise NotImplementedError("Class %s doesn't implement this method" % self.__class__.__name__)

    def _find_checksum_keyword(self, digestfile):
        line = "-"
        while line != "" and self.CHECKSUM_KEYWORD not in line:
            line = digestfile.readline().decode()
        return self.CHECKSUM_KEYWORD in line

    def _verify(self):
        BLOCKSIZE = 65536
        hasher = self._verify_hasher()
        with open(self._target_file, "rb") as targetfile:
            buf = targetfile.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = targetfile.read(BLOCKSIZE)

        with open(self._checkum_file, "rb") as digestfile:
            if self._find_checksum_keyword(digestfile):
                expected = digestfile.readline().decode().split(" ")[0]
                return expected == hasher.hexdigest()
            else:
                log.critical("Could not find %s checksum in %s" % (self.CHECKSUM_KEYWORD, digestfile.name))
                return False

    def _clean(self):
        for filepath in [self._target_file, self._checkum_file]:
            if os.path.exists(filepath):
                log.debug("Renaming %s" % filepath)
                os.rename(filepath, "%s.old" % filepath)

    def _download(self):
        if os.path.exists(self._target_file):
            if self.overwrite:
                log.info("Chose to overwrite old files.")
                self._clean()
            elif not self.verify():
                log.error("Previous download seems corrupted.")
                self._clean()
            else:
                log.info("Using previously downloaded %s" % self.filename)
                return self.filename
        elif not os.path.exists(self.directory):
            log.debug("Creating %s" % self.directory)
            os.mkdir(self.directory)

        try:
            for filename in [self.filename, self.filename + self.CHECKSUM_SUFFIX]:
                log.debug("Downloading %s" % filename)
                wget.download(self.base_url + filename, out=self.directory, bar=None)
            if self.verify():
                log.debug(("Successfully downloaded: %s" % filename))
                return self._target_file
            else:
                return None
        except Exception as e:
            log.debug("Failed to download %s: %s" % (filename, e))

    def download(self):
        if self.date is None:
            log.debug("Assuming today for archive date")
            self.date = datetime.datetime.today().strftime("%Y%m%d")

        day = datetime.datetime.strptime(self.date, "%Y%m%d")

        for i in list(range(1+self.history)):
            self.date = (day-datetime.timedelta(days=i)).strftime("%Y%m%d")
            filename = self._download()
            if filename is not None:
                return filename

        log.warning("Could not find a valid file between %s and %s" % (self.date, day.strftime("%Y%m%d")))
        return None


    def verify(self):
        result = False
        try:
            result = self._verify()
            result_string = { False: ":-(", True: ":-)" }
            log.debug("Checksum verification of %s: %s" % (self.filename, result_string[result]))
        except Exception as e:
            log.critical("%s" % e)
        return result

class Stage3Downloader(Downloader):
    @property
    def BASE_URL(self):
        return Template("http://distfiles.gentoo.org/releases/$arch/autobuilds/$date/")

    @property
    def FILENAME(self):
        return Template("stage3-$subarch-$date.tar.bz2")

    @property
    def CHECKSUM_SUFFIX(self):
        return ".DIGESTS"

    @property
    def CHECKSUM_KEYWORD(self):
        return "SHA512 HASH"

    def _verify_hasher(self):
        return hashlib.sha512()


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

    @property
    def CHECKSUM_KEYWORD(self):
        return "MD5 HASH"

    def _verify_hasher(self):
        return hashlib.md5()

    def _find_checksum_keyword(self, digestfile):
        return True


def download(args):
    if args.stage3:
        stage3_downloader = Stage3Downloader(args.date, args.arch, args.directory, args.overwrite, subarch=args.subarch, history=args.history)
        stage3_downloader.download()

    if args.portage:
        portage_downloader = PortageDownloader(args.date, args.arch, args.directory, args.overwrite, history=args.history)
        portage_downloader.download()

def verify(args):
    if args.stage3:
        stage3_downloader = Stage3Downloader(args.date, args.arch, args.directory, subarch=args.subarch)
        stage3_downloader.verify()

    if args.portage:
        portage_downloader = PortageDownloader(args.date, args.arch, args.directory)
        portage_downloader.verify()

def main():
    parser = argparse.ArgumentParser(description="Utility for retrieving Gentoo stage3+portage archives")
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('-v', '--verbosity', action="count", default=0,
                        help="increase output verbosity (e.g., -vv is more than -v)")
    parser.add_argument('--history', type=int, default=60, help="Days to attempt to go back from the specified or assumed date")

    parser_stage3group = parser.add_argument_group()
    parser.add_argument("--directory", nargs="?", default="download/", help="Directory for file downloads and verifications. Defaults to 'download/'")
    parser_stage3group.add_argument("--stage3", action="store_true", default=False, help="Process stage3 archive")
    parser_stage3group.add_argument("--arch", nargs="?", default="amd64", help="ARCH for stage3 archive. Defaults to 'amd64'")
    parser_stage3group.add_argument("--subarch", nargs="?", help="SUBARCH for stage3 archive")
    parser_portagegroup = parser.add_argument_group()
    parser_portagegroup.add_argument("--portage", action="store_true", default=False, help="Process portage snapshot")

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
    log.basicConfig(format="%(levelname)s: %(message)s", level=get_loglevel(args.verbosity))
    args.func(args)