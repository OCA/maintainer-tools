#!/usr/bin/env python

from github3 import login
from getpass import getuser, getpass

MAINTAINERS_TEAM_ID = 844365
BLACKLIST = [MAINTAINERS_TEAM_ID,
             829420  # 'Owners' team
             ]


def main():
    # user = getuser()
    user = 'guewen'

    password = ''
    while not password:
        password = getpass('Password for {0}: '.format(user))

    gh = login(user, password=password)

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
        print "Team %s" % team.name
        missing = maintainers - team_members
        if not missing:
            print "All maintainers are registered"
        for member in missing:
            print "Adding %s" % member.login
            team.add_member(member.login)


if __name__ == '__main__':
    main()
