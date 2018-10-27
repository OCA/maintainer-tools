import re
import os
import subprocess
import fileinput
import sys
import shutil
import pdb

# Runbot urls need the repo id from the table in the runbot server.
# This file is the output of a select id, name from there.
for repo_list_line in open('repos_with_ids.txt'):
    m = re.search(r'(\d+)\|github.com/OCA/(.*)', repo_list_line)
    repo_name = m.group(2)
    repo_id = m.group(1)
    print(repo_name)
    if not os.path.exists(repo_name):
        subprocess.call(['hub', 'clone', '--quiet', 'OCA/' + repo_name])

    os.chdir(repo_name)
    for version in ['6.1', '7.0', '8.0']:
        try:
            subprocess.check_call(['git', 'checkout', '--quiet', version])
        except subprocess.CalledProcessError:
            continue

        subprocess.check_call(['git', 'reset', '--hard'])
        subprocess.check_call(['git', 'clean', '-fxd'])
        new_lines = (
            "[![Runbot Build Status]"
            "(http://runbot.odoo-community.org/runbot/badge/flat/{0}/{1}.svg)]"
            "(http://runbot.odoo-community.org/runbot/repo/{0})\n".format(
                repo_id, version
            )
        )

        # template file is in OCA/maintainer-quality-tools
        if not os.path.exists('.codeclimate.yml'):
            new_lines += (
                "[![Code Climate]"
                "(https://codeclimate.com/github/OCA/{0}/badges/gpa.svg)]"
                "(https://codeclimate.com/github/OCA/{0})\n".format(
                    repo_name
                )
            )
            shutil.copy('../.codeclimate.yml', '.')

        # template file is in OCA/maintainer-quality-tools
        if not os.path.exists('CONTRIBUTING.md'):
            shutil.copy('../CONTRIBUTING.md', '.')

        stuff_added = False
        for readme_line in fileinput.input('README.md', inplace=1):
            sys.stdout.write(readme_line)
            if not stuff_added and 'travis-ci.org' in readme_line:
                sys.stdout.write(new_lines)
                stuff_added = True

        subprocess.check_call(['git', 'add', '--all'])
        subprocess.check_call(
            ['git', 'commit', '-m',
             '''\
add badges and files for runbot, codeclimate

This is an automatic commit done with the add-badges.py script
in maintainers-tools.
''']
        )

        # stop here!
        pdb.set_trace()

    os.chdir('..')
