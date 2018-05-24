# Copyright (c) 2016-2018 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
from __future__ import print_function
import contextlib
import dumbdbm
import logging
import os
import subprocess
from ConfigParser import RawConfigParser

from wheel.install import WheelFile
from pkg_resources import parse_version

import click

_logger = logging.getLogger(__name__)


REGISTER_RETRY = 2


def _split_filename(filename):
    """ Split a .whl or .tar.gz distribution file name
    into a (package_name, version) tuple

    >>> _split_filename('abc-1.1.tar.gz')
    ('abc', <Version('1.1')>)
    >>> _split_filename('dir/abc-1.1.tar.gz')
    ('abc', <Version('1.1')>)
    >>> _split_filename('a_bc-1.1.tar.gz')
    ('a-bc', <Version('1.1')>)
    >>> _split_filename('a_b-c-1.1.tar.gz')
    ('a-b-c', <Version('1.1')>)
    >>> _split_filename('mis_builder-3.1.1.99.dev17-py2-none-any.whl')
    ('mis-builder', <Version('3.1.1.99.dev17')>)
    >>> _split_filename('a/b/mis_builder-3.1.1.99.dev17-py2-none-any.whl')
    ('mis-builder', <Version('3.1.1.99.dev17')>)
    """
    basename = os.path.basename(filename)
    if basename.endswith('.whl'):
        wheelfile = WheelFile(basename)
        package_name = wheelfile.parsed_filename.group('name')
        package_ver = wheelfile.parsed_filename.group('ver')
    elif basename.endswith('.tar.gz'):
        package_ver = basename.split('-')[-1][:-7]
        package_name = basename[:-(len(package_ver) + 8)]
    else:
        raise RuntimeError("Unrecognized file type %s" % (filename,))
    package_name = package_name.replace('_', '-')
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
        if parser.has_option(repository, 'repository'):
            self.repository_url = parser.get(repository, 'repository')
        else:
            # this is the legacy pypi url that we use in the cache keys
            self.repository_url = 'https://pypi.python.org/pypi'
        self.cache = cache
        self.dryrun = dryrun

    def _make_key(self, distfilename):
        return str(self.repository_url + '#' + os.path.basename(distfilename))

    def _key_match(self, key):
        return key.startswith(self.repository_url + '#')

    def _key_to_wheel(self, key):
        return key[len(self.repository_url) + 1:]

    def _upload(self, distfilename):
        cmd = ['twine', 'upload', '--config-file', self.pypirc,
               '-r', self.repository, '--skip-existing', distfilename]
        if not self.dryrun:
            try:
                subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                if "HTTPError: 400 Client Error" in e.output:
                    return e.output
                print(e.output)
                raise
        else:
            _logger.info("dryrun: %s", cmd)

    def upload_dist(self, distfilename, dbm):
        key = self._make_key(distfilename)
        if key in dbm:
            value = dbm[key]
            detail = '' if not value else ' (with error)'
            _logger.debug("skipped %s: found in cache%s",
                          distfilename, detail)
            return
        _logger.info("uploading %s to %s",
                     distfilename, self.repository)
        r = self._upload(distfilename)
        if r:
            _logger.error("uploading %s to %s failed: %s",
                          distfilename, self.repository, r)
        if not self.dryrun:
            dbm[key] = r or ''
        else:
            _logger.info("dryrun: caching %s: %s", key, (r or ''))

    def upload_dists(self, distfilenames):
        to_upload = []
        for distfilename in distfilenames:
            if os.path.isfile(distfilename) and \
                    (distfilename.lower().endswith('.whl') or
                     distfilename.lower().endswith('.tar.gzXXX')):
                to_upload.append(distfilename)
            else:
                _logger.debug("skipped %s: not a python distribution",
                              distfilename)
        with contextlib.closing(dumbdbm.open(self.cache, 'c')) as dbm:
            for distfilename in sorted(to_upload, key=_split_filename):
                self.upload_dist(distfilename, dbm)

    def cache_print_errors(self):
        with contextlib.closing(dumbdbm.open(self.cache, 'r')) as dbm:
            for key, value in dbm.items():
                if not self._key_match(key):
                    continue
                if value:
                    wheel = self._key_to_wheel(key)
                    click.echo(u"{}: {}".format(wheel, value))

    def cache_rm(self, distfilenames):
        with contextlib.closing(dumbdbm.open(self.cache, 'w')) as dbm:
            for distfilename in distfilenames:
                distfilename = os.path.basename(distfilename)
                key = self._make_key(distfilename)
                if key in dbm:
                    del dbm[key]


@click.group()
@click.option('--pypirc', required=True)
@click.option('--repository', required=True)
@click.option('--cache', required=True)
@click.option('--dryrun/--no-dryrun', default=False)
@click.option('--debug/--no-debug', default=False)
@click.option('--quiet/--no-quiet', default=False)
@click.pass_context
def cli(ctx, pypirc, repository, cache, dryrun, debug, quiet):
    if debug:
        level = logging.DEBUG
    else:
        if not quiet:
            level = logging.INFO
        else:
            level = logging.WARNING
    logging.basicConfig(
        format='%(asctime)s:%(levelname)s:%(message)s',
        level=level)
    ctx.obj = OcaPypi(pypirc, repository, cache, dryrun)


@click.command()
@click.argument('dists', nargs=-1)
@click.option('--dist-dir',
              help="Directory that is walked recursively to "
                   "find .whl and .tar.gz files to upload.")
@click.pass_context
def upload(ctx, dists, dist_dir):
    if dists:
        ctx.obj.upload_dists(dists)
    if dist_dir:
        for dirpath, _, filenames in os.walk(dist_dir):
            ctx.obj.upload_dists([
                os.path.join(dirpath, filename)
                for filename in filenames
            ])


@click.command()
@click.pass_context
def cache_print_errors(ctx):
    ctx.obj.cache_print_errors()


@click.command()
@click.argument('dists', nargs=-1)
@click.pass_context
def cache_rm(ctx, dists):
    ctx.obj.cache_rm(dists)


cli.add_command(upload)
cli.add_command(cache_print_errors)
cli.add_command(cache_rm)


if __name__ == '__main__':
    cli()
