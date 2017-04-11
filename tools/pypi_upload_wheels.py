import anydbm
import contextlib
import logging
import os
import requests
import subprocess
import time
from wheel.install import WheelFile
from ConfigParser import RawConfigParser
from pkg_resources import parse_version

import click

_logger = logging.getLogger(__name__)


REGISTER_RETRY = 2


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

    def _make_reg_key(self, wheelfilename):
        package_name, _ = _split_wheelfilename(wheelfilename)
        return str(self.repository_url + '#' + package_name)

    def _make_key(self, wheelfilename):
        return str(self.repository_url + '#' + os.path.basename(wheelfilename))

    def _key_match(self, key):
        return key.startswith(self.repository_url + '#')

    def _key_to_wheel(self, key):
        return key[len(self.repository_url) + 1:]

    def _registered(self, wheelfilename):
        package_name, package_ver = _split_wheelfilename(wheelfilename)
        package_url = self.repository_url + '/' + package_name
        r = requests.head(package_url)
        return r.status_code == 200

    def _register(self, wheelfilename):
        cmd = ['twine', 'register', '--config-file', self.pypirc,
               '-r', self.repository, wheelfilename]
        if not self.dryrun:
            retry = REGISTER_RETRY
            while True:
                try:
                    subprocess.check_output(cmd, stderr=subprocess.STDOUT)
                    break  # success
                except subprocess.CalledProcessError as e:
                    if "HTTPError: 400 Client Error" in e.output:
                        return e.output  # unrecoverable error
                    else:
                        retry -= 1
                        if retry > 0:
                            _logger.warning("error registering %s, retrying" %
                                            (wheelfilename, ))
                            time.sleep(5)
                        else:
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
        key = self._make_key(wheelfilename)
        with contextlib.closing(anydbm.open(self.cache, 'c')) as dbm:
            if key in dbm:
                value = dbm[key]
                detail = '' if not value else ' (with error)'
                _logger.debug("skipped %s: found in cache%s",
                              wheelfilename, detail)
                return
            reg_key = self._make_reg_key(wheelfilename)
            if reg_key not in dbm and not self._registered(wheelfilename):
                _logger.info("registering %s to %s",
                             wheelfilename, self.repository_url)
                r = self._register(wheelfilename)
                if r:
                    # registration failed, store the error in cache
                    # so we don't try again, and do not try to upload
                    _logger.error("registering %s to %s failed: %s",
                                  wheelfilename, self.repository_url, r)
                    if not self.dryrun:
                        dbm[key] = r
                    return
                else:
                    if not self.dryrun:
                        dbm[reg_key] = ''
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
                _logger.warn("skipped %s: not a wheel file", wheelfilename)
        for wheelfilename in sorted(to_upload, key=_split_wheelfilename):
            self.upload_wheel(wheelfilename)

    def cache_print_errors(self):
        with contextlib.closing(anydbm.open(self.cache, 'r')) as dbm:
            for key, value in dbm.items():
                if not self._key_match(key):
                    continue
                if value:
                    wheel = self._key_to_wheel(key)
                    click.echo(u"{}: {}".format(wheel, value))

    def cache_rm_wheels(self, wheelfilenames):
        with contextlib.closing(anydbm.open(self.cache, 'w')) as dbm:
            for wheelfilename in wheelfilenames:
                wheelfilename = os.path.basename(wheelfilename)
                key = self._make_key(wheelfilename)
                if key in dbm:
                    del dbm[key]


@click.group()
@click.option('--pypirc', required=True)
@click.option('--repository', required=True)
@click.option('--cache', required=True)
@click.option('--dryrun/--no-dryrun', default=False)
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, pypirc, repository, cache, dryrun, debug):
    if debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(
        format='%(asctime)s:%(levelname)s:%(message)s',
        level=level)
    ctx.obj = OcaPypi(pypirc, repository, cache, dryrun)


@click.command()
@click.argument('wheels', nargs=-1)
@click.pass_context
def upload(ctx, wheels):
    ctx.obj.upload_wheels(wheels)


@click.command()
@click.pass_context
def cache_print_errors(ctx):
    ctx.obj.cache_print_errors()


@click.command()
@click.argument('wheels', nargs=-1)
@click.pass_context
def cache_rm_wheels(ctx, wheels):
    ctx.obj.cache_rm_wheels(wheels)


cli.add_command(upload)
cli.add_command(cache_print_errors)
cli.add_command(cache_rm_wheels)


if __name__ == '__main__':
    cli()
