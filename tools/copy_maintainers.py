# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

from .github_login import login


MAINTAINERS_TEAM_ID = 844365
BLACKLIST = [MAINTAINERS_TEAM_ID,
             829420  # 'Owners' team
             ]


def main():
    gh = login()

    org = gh.organization('oca')

    teams = org.iter_teams()
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


if __name__ == '__main__':
    main()
