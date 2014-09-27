# gen2fetcher
A utility that allows downloading and verifying Gentoo stage3 and portage-snapshot archives.


## Early Stage Warning
The API and command line arguments will eventually break in upcoming versions!

## Installation
If you want to try gen2fetcher you can install it via *pip*. I suggest using pip inside [virtualenv](https://github.com/pypa/virtualenv).

```
pip install -r https://raw.githubusercontent.com/steveeJ/gen2fetcher/master/requirements.txt
```

## Usage

### Overview
```
$ gen2fetcher --help
usage: gen2fetcher [-h] [--arch [ARCH]] [--stage3] [--portage]
                   [--directory [DIRECTORY]]
                   {download,verify} ...

Utility for retrieving Gentoo stage3+portage archives

positional arguments:
  {download,verify}

optional arguments:
  -h, --help            show this help message and exit
  --arch [ARCH]         ARCH for stage3 archive. Defaults to 'amd64'
  --stage3              Process stage3 archive
  --portage             Process portage snapshot
  --directory [DIRECTORY]
                        Directory for file downloads. Defaults to 'download/'
```

### download command
```
$ gen2fetcher download --help
usage: gen2fetcher download [-h] [--date DATE] [-o]

optional arguments:
  -h, --help       show this help message and exit
  --date DATE      Request a specific archive date.
  -o, --overwrite
```

### verify command
```
$ gen2fetcher verify --help
usage: gen2fetcher verify [-h] --date DATE

optional arguments:
  -h, --help   show this help message and exit
  --date DATE  Request a specific archive date.
```

## Example
This is an example of downloading the most recent stage3 and portage archive,
where the stage3 archive was already in place.

```
$ gen2fetcher --stage3 --portage download
DEBUG: Assuming today for archive date
INFO: Downloading stage3-amd64-20140926.tar.bz2
ERROR: Failed to download stage3-amd64-20140926.tar.bz2
Cannot download //distfiles.gentoo.org/releases/amd64/autobuilds/20140926/stage3-amd64-20140926.tar.bz2:
404: Not Found
INFO: Checksum verification of stage3-amd64-20140925.tar.bz2: :-)
INFO: Using previously downloaded stage3-amd64-20140925.tar.bz2
DEBUG: Assuming today for archive date
INFO: Downloading portage-20140926.tar.xz
[..................................................................................................]
INFO: Downloading portage-20140926.tar.xz.md5sum
[..................................................................................................]
INFO: Checksum verification of portage-20140926.tar.xz: :-)
```
