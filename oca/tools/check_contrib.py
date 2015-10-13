#!/usr/bin/python
from __future__ import division

import subprocess
import itertools
import operator
import argparse
import os.path as osp
import sys

from oca_projects import OCA_PROJECTS, url


def get_contributions(projects, since, merges):
    cmd = ['git', 'log', '--pretty=format:%ai %ae']
    if since is not None:
        cmd += ['--since', since]
    if merges:
        cmd += ['--merges']
    if isinstance(projects, (str, unicode)):
        projects = [projects]
    for project in projects:
        contributions = {}
        for repo in OCA_PROJECTS[project]:
            if not osp.isdir(repo):
                status = subprocess.call(['git', 'clone', '--quiet',
                                          url(repo), repo])
                if status != 0:
                    sys.stderr.write("%s not found on github\n" % repo)
                    continue
            pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=repo)
            out, error = pipe.communicate()
            for line in out.splitlines():
                try:
                    date, hour, tz, author = line.split()
                except ValueError:
                    sys.stderr.write('error parsing line:\n%s\n' % line)
                    continue
                contributions.setdefault(author, []).append(date)
        yield project, contributions


def top_contributors(projects, since=None, merges=False, top=5):
    for project, contributions in get_contributions(projects, since, merges):
        contributors = sorted(contributions.iteritems(),
                              key=lambda x: len(x[1]),
                              reverse=True)
        nb_contribs = sum(len(contribs) for author, contribs in contributors)
        for author, contribs in contributors[:top]:
            yield (project, author, len(contribs),
                   len(contribs) / nb_contribs, min(contribs), max(contribs))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--since',
                        metavar='YYYY-MM-DD',
                        default=None,
                        help='only consider contributions since YYYY-MM-DD')
    parser.add_argument('--merges',
                        default=False,
                        action='store_true',
                        help='only consider merges')
    parser.add_argument('--nb-contrib',
                        default=5,
                        type=int,
                        help='number of contributors to consider')
    parser.add_argument('--csv',
                        default=False,
                        action='store_true',
                        help='produce CSV output')

    project_names = sorted(OCA_PROJECTS)
    args = parser.parse_args()
    grouped = itertools.groupby(top_contributors(project_names,
                                                 since=args.since,
                                                 merges=args.merges,
                                                 top=args.nb_contrib),
                                operator.itemgetter(0))
    if args.csv:
        print 'project,author,nb contrib,nb contrib(%),earliest,latest'
        template = '%(project)s,%(author)s,%(nb_contrib)d,' \
                   '%(percent_contrib).0f,%(earliest)s,%(latest)s'
    else:
        template = '     %(author)-35s:\t%(nb_contrib) 4d' \
                   ' [%(percent_contrib) 3.0f%%] %(earliest)s %(latest)s'
    for project, contribs in grouped:
        if not args.csv:
            print project
        for (_p, author, nb_contrib, percent_contrib,
             earliest, latest) in contribs:
            info = {'project': project,
                    'author': author,
                    'percent_contrib': percent_contrib * 100,
                    'nb_contrib': nb_contrib,
                    'earliest': earliest,
                    'latest': latest}
            print template % info
        if not args.csv:
            print

if __name__ == "__main__":
    main()
