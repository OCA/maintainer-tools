# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import argparse
import sys
from operator import attrgetter
from . import github_login
from . import odoo_login
from . import colors


def copy_users(odoo, team=None, dry_run=False):
    gh = github_login.login()

    # on odoo, the model is a project, but they are teams on GitHub
    Project = odoo.model('project.project')
    if team:
        projects = Project.browse([('name', '=', team)])
        if not projects:
            sys.exit('Project %s not found.' % team)
    else:
        projects = Project.browse([])

    print('Fetching teams...')
    org = gh.organization('oca')
    github_teams = list(org.iter_teams())
    valid = []
    not_found = []
    for odoo_project in sorted(projects, key=attrgetter('name')):
        for github_team in github_teams:
            if github_team.name == odoo_project.name:
                valid.append((odoo_project, github_team))
                break
        else:
            not_found.append(odoo_project)

    no_github_login = set()
    for odoo_project, github_team in valid:
        print()
        print('Syncing project "%s"' % odoo_project.name)
        users = [odoo_project.user_id]
        users += odoo_project.members
        logins = set()
        for user in users:
            if user.x_github_login:
                logins.add(user.x_github_login)
            else:
                no_github_login.add("%s (%s)" % (user.name, user.login))
        current_logins = set(user.login for user in github_team.iter_members())

        keep_logins = logins.intersection(current_logins)
        remove_logins = current_logins - logins
        add_logins = logins - current_logins
        print("Add   ", colors.GREEN + ', '.join(add_logins) + colors.ENDC)
        print("Keep  ", ', '.join(keep_logins))
        print("Remove", colors.FAIL + ', '.join(remove_logins) + colors.ENDC)
        if not dry_run:
            for login in add_logins:
                github_team.add_member(login)
            for login in remove_logins:
                github_team.remove_member(login)

    if no_github_login:
        print()
        print('Following users miss GitHub login:')
        print(colors.FAIL + '\n'.join(user for user in no_github_login) +
              colors.ENDC)

    if not_found:
        print()
        print('The following odoo projects have no team in GitHub:')
        for project in not_found:
            print(project.name)


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
