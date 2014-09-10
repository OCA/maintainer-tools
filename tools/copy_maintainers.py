# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import argparse
import sys
from . import github_login
from . import odoo_login


MAINTAINERS_TEAM_ID = 844365
BLACKLIST = [MAINTAINERS_TEAM_ID,
             829420  # 'Owners' team
             ]


def copy_users(odoo, team=None, dry_run=False):
    gh = github_login.login()

    # called Project on odoo, but we use 'team' as in GitHub
    Project = odoo.model('project.project')
    if team:
        projects = Project.browse([('name', '=', team)])
        if not projects:
            sys.exit('Project %s not found.' % team)
    else:
        projects = Project.browse([])

    org = gh.organization('oca')
    for project in projects:
        name = project.name
        print('Syncing %s' % name)
        teams = list(org.iter_teams())


    sys.exit('not implemented')

    maintainers_team = next((team for team in teams if
                            team.id == MAINTAINERS_TEAM_ID),
                            None)
    assert maintainers_team, "Maintainers Team not found"

    maintainers = set(maintainers_team.iter_members())

    for team in teams:
        if team.id in BLACKLIST:
            continue
        team_members = set(team.iter_members())
        print("Team {0}".format(team.name))
        missing = maintainers - team_members
        if not missing:
            print("All maintainers are registered")
        for member in missing:
            print("Adding {0}".format(member.login))
            team.add_member(member.login)


def main():
    parser = argparse.ArgumentParser(parents=[odoo_login.get_parser()])
    group = parser.add_argument_group('Copy maintainers options')
    group.add_argument("-t", "--team",
                       help="Name of the team to synchronize.")
    group.add_argument("--dry-run",
                       action='store_true',
                       help="Prints the actions to do, "
                            "but does not apply them")
    args = parser.parse_args()

    odoo = odoo_login.login(args.username, args.store)
    copy_users(odoo, team=args.team, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
