# -*- coding: utf-8 -*-
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
from __future__ import absolute_import, print_function

"""
oca-copy-maintainers

Copy the users from the teams configured on community.odoo.com to the
GitHub teams

"""

import argparse
import errno
import os
import sys
from operator import attrgetter
from . import github_login
from . import odoo_login
from . import colors


COPY_USERS_BLACKLIST = os.environ.get(
    "COPY_USERS_BLACKLIST", "~/.config/oca-copy-maintainers/copy_users_blacklist.txt"
)


class FakeProject(object):
    """mock project to represent the 'CLA' team"""

    def __init__(self, name, members):
        self.name = name
        self._members = members

    @property
    def user_id(self):
        return False
        return self._members[0] if self._members else False

    @property
    def members(self):
        return self._members[1:]


def get_cla_project(odoo):
    Partner = odoo.model("res.partner")
    domain = [
        ("github_name", "!=", False),
        "|",
        ("category_id.name", "in", ("ECLA", "ICLA")),
        ("parent_id.category_id.name", "=", "ECLA"),
    ]
    members = Partner.browse(domain)
    return FakeProject("OCA Contributors", members)


class GHTeamList(object):
    def __init__(self, gh_cnx=None, org="oca", dry_run=False):
        if gh_cnx is None:
            gh_cnx = github_login.login()
        self._gh = gh_cnx
        self._org = self._gh.organization("oca")
        self._load_teams()
        self.dry_run = dry_run

    def _load_teams(self):
        self._teams = {t.name: t for t in self._org.teams()}

    def get_project_team(self, project):
        team = self._teams.get(project.name)
        if team:
            return team
        team = self._teams.get(project.name + " Maintainers")
        if team:
            return team
        team = self._teams.get("Local " + project.name + " Maintainers")
        return team

    def get_project_psc_team(self, project):
        main_team = self.get_project_team(project)
        if not main_team:
            return None
        name = main_team.name + " PSC Representative"
        team = self._teams.get(name)
        if team is None and main_team is not None:
            team = self.create_psc_team(project, name, main_team)
        # sync repositories
        if team:
            for repo in main_team.repositories():
                repo_name = "%s/%s" % (repo.owner.login, repo.name)
                if not team.has_repository(repo_name):
                    if not self.dry_run:
                        status = team.add_repository(repo_name)
                    else:
                        status = False
                    print(
                        "Added repo %s to team %s -> %s"
                        % (repo_name, team.name, "OK" if status else "NOK")
                    )
        if team:
            print(list(r.name for r in team.repositories()))
        else:
            print("no team found for project %", project)
        return team

    def create_psc_team(self, project, team_name, main_team):
        repo_names = [
            "%s/%s" % (r.owner.login, r.name) for r in main_team.repositories()
        ]
        if not self.dry_run:
            self._org.create_team(name=team_name, repo_names=repo_names)
        self._load_teams()
        return self._teams.get(team_name)


def get_members_project(odoo):
    Partner = odoo.model("res.partner")
    domain = [
        ("github_name", "!=", False),
        ("membership_state", "in", ("paid", "free")),
    ]
    members = Partner.browse(domain)
    return FakeProject("OCA Members", members)


def get_copy_users_blacklist(filename=COPY_USERS_BLACKLIST):
    """read the blacklist file, if it exists (tries to create one if none).
    File format 1 github login per line, comments begin with # until end of line
    """
    try:
        fobj = open(filename)
    except IOError as exc:
        if exc.errno == errno.ENOENT:  # no such file or directories
            os.makedirs(os.path.dirname(filename))
            fobj = open(filename, "w")
            fobj.close()
            fobj = open(filename)
        else:
            raise
    blacklist = set()
    for line in fobj:
        login = line.split("#", 1)[0].strip().lower()
        blacklist.add(login)
    return blacklist


def copy_users(odoo, team=None, dry_run=False):
    gh = github_login.login()

    # on odoo, the model is a project, but they are teams on GitHub
    Project = odoo.model("project.project")
    base_domain = [
        ("privacy_visibility", "!=", "followers"),
    ]
    if team == "OCA Contributors":
        projects = [get_cla_project(odoo)]
    elif team == "OCA Members":
        projects = [get_members_project(odoo)]
    elif team:
        domain = [("name", "=", team)] + base_domain
        projects = Project.browse(domain)
        if not projects:
            sys.exit("Project %s not found. (%s)" % (team, domain))
    else:
        projects = list(Project.browse(base_domain))
        projects.append(get_cla_project(odoo))
        projects.append(get_members_project(odoo))
    github_teams = GHTeamList(gh, org="oca", dry_run=dry_run)
    valid = []
    not_found = []
    for odoo_project in sorted(projects, key=attrgetter("name")):
        team = github_teams.get_project_team(odoo_project)
        if team and odoo_project.user_id:
            psc_team = github_teams.get_project_psc_team(odoo_project)
        else:
            psc_team = False
        if team:
            valid.append((odoo_project, team, psc_team))
        else:
            not_found.append(odoo_project)

    black_list = get_copy_users_blacklist()

    no_github_login = set()
    for odoo_project, github_team, psc_team in valid:
        print()
        print('Syncing project "%s"' % odoo_project.name)
        psc_users = [odoo_project.user_id] if odoo_project.user_id else []
        users = psc_users + list(odoo_project.members)
        user_logins = set(
            [
                "oca-transbot",
                "OCA-git-bot",
                "oca-travis",
            ]
        )
        psc_user_logins = set()
        for user in users:
            if user.github_name:
                if user.github_name.lower() not in black_list:
                    user_logins.add(user.github_name)
            else:
                no_github_login.add("%s (%s)" % (user.name, user.login))
        for user in psc_users:
            if user.github_name and user.github_name not in black_list:
                psc_user_logins.add(user.github_name)
        sync_team(github_team, user_logins, dry_run)
        if psc_team:
            sync_team(psc_team, psc_user_logins, dry_run)

    if no_github_login:
        print()
        print("Following users miss GitHub login:")
        print(colors.FAIL + "\n".join(no_github_login) + colors.ENDC)

    if not_found:
        print()
        print("The following Odoo projects have no team in GitHub:")
        for project in not_found:
            print(project.name)


def sync_team(team, logins, dry_run=False):
    print(team.name)
    current_logins = set(user.login for user in team.members())

    keep_logins = logins.intersection(current_logins)
    remove_logins = current_logins - logins
    add_logins = logins - current_logins
    print("Add   ", (colors.GREEN + ", ".join(add_logins) + colors.ENDC))
    print("Keep  ", ", ".join(keep_logins))
    print("Remove", (colors.FAIL + ", ".join(remove_logins) + colors.ENDC))
    if not dry_run:
        for login in add_logins:
            try:
                team.add_or_update_membership(login)
            except Exception as exc:
                print("Failed to invite %s: %s" % (login, exc))
        for login in remove_logins:
            try:
                team.remove_member(login)
            except Exception as exc:
                print("Failed to remove %s: %s" % (login, exc))


def main():
    parser = argparse.ArgumentParser(parents=[odoo_login.get_parser()])
    group = parser.add_argument_group("Copy maintainers options")
    group.add_argument("-t", "--team", help="Name of the team to synchronize.")
    group.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Prints the actions to do, " "but does not apply them",
    )
    args = parser.parse_args()

    odoo = odoo_login.login(args.username, args.store)
    copy_users(odoo, team=args.team, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
