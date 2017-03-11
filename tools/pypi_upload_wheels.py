import anydbm
import argparse
import contextlib
import logging
import os
import requests
import subprocess
from wheel.install import WheelFile
from ConfigParser import RawConfigParser
from pkg_resources import parse_version

_logger = logging.getLogger(__name__)


def _split_wheelfilename(wheelfilename):
    wheelfile = WheelFile(wheelfilename)
    package_name = wheelfile.parsed_filename.group('name')
    package_name = package_name.replace('_', '-')
    package_ver = wheelfile.parsed_filename.group('ver')
    package_ver = parse_version(package_ver)
    return package_name, package_ver


class OcaPypi(object):
    """A wrapper around twine, with caching
    to avoid multiple useless upload attempts for the same file."""

    def __init__(self, pypirc, repository, cache, dryrun):
        parser = RawConfigParser()
        parser.read(pypirc)
        self.pypirc = pypirc
        self.repository = repository
        self.repository_url = parser.get(repository, 'repository')
        self.cache = cache
        self.dryrun = dryrun

    def _registered(self, wheelfilename):
        package_name, package_ver = _split_wheelfilename(wheelfilename)
        package_url = self.repository_url + '/' + package_name
        r = requests.head(package_url)
        return r.status_code == 200

    def _register(self, wheelfilename):
        cmd = ['twine', 'register', '--config-file', self.pypirc,
               '-r', self.repository, wheelfilename]
        if not self.dryrun:
            try:
                subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                if "HTTPError: 400 Client Error" in e.output:
                    return e.output
                raise
        else:
            _logger.info("dryrun: %s", cmd)

    def _upload(self, wheelfilename):
        cmd = ['twine', 'upload', '--config-file', self.pypirc,
               '-r', self.repository, '--skip-existing', wheelfilename]
        if not self.dryrun:
            try:
                subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                if "HTTPError: 400 Client Error" in e.output:
                    return e.output
                raise
        else:
            _logger.info("dryrun: %s", cmd)

    def upload_wheel(self, wheelfilename):
        key = self.repository_url + '#' + os.path.basename(wheelfilename)
        with contextlib.closing(anydbm.open(self.cache, 'c')) as dbm:
            if key in dbm:
                _logger.debug("skipped %s: found in cache", wheelfilename)
                return
            if not self._registered(wheelfilename):
                _logger.info("registering %s to %s",
                             wheelfilename, self.repository_url)
                r = self._register(wheelfilename)
                if r:
                    # registration failed, store the error in cache
                    # so we don't try again, and do not try to upload
                    _logger.error("registering %s to %s failed: %s",
                                  wheelfilename, self.repository_url, r)
                    if not self.dryrun:
                        dbm[key] = r or ''
                    return
            _logger.info("uploading %s to %s",
                         wheelfilename, self.repository_url)
            r = self._upload(wheelfilename)
            if r:
                _logger.error("uploading %s to %s failed: %s",
                              wheelfilename, self.repository_url, r)
            if not self.dryrun:
                dbm[key] = r or ''

    def upload_wheels(self, wheelfilenames):
        to_upload = []
        for wheelfilename in wheelfilenames:
            if os.path.isfile(wheelfilename) and \
                    wheelfilename.lower().endswith('.whl'):
                to_upload.append(wheelfilename)
            else:
                _logger.debug("skipped %s: not a wheel file", wheelfilename)
        for wheelfilename in sorted(to_upload, key=_split_wheelfilename):
            self.upload_wheel(wheelfilename)


def main():
    logging.basicConfig(
        format='%(asctime)s:%(levelname)s:%(message)s',
        level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="OCA Twine Wrapper")
    parser.add_argument('--pypirc', required=True)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--cache', required=True)
    parser.add_argument('--dryrun', action='store_true')
    parser.add_argument('wheels', nargs='+')
    args = parser.parse_args()
    pypi = OcaPypi(args.pypirc, args.repository, args.cache, args.dryrun)
    pypi.upload_wheels(args.wheels)


if __name__ == '__main__':
    main()
