import re
import os
import subprocess
import fileinput
import sys
import shutil

for repo_list_line in open('repositories.txt'):
    m = re.search('(\d+)\|github.com/OCA/(.*)', repo_list_line)
    repo_name = m.group(2)
    repo_id = m.group(1)
    print(repo_name)
    if not os.path.exists(repo_name):
        subprocess.call(['hub', 'clone', '--quiet', 'OCA/' + repo_name])

    os.chdir(repo_name)
    for version in ['6.1', '7.0', '8.0']:
        try:
            subprocess.check_call(['git', 'checkout', '--quiet', version])
            subprocess.check_call(['git', 'reset', '--hard'])
            subprocess.check_call(['git', 'clean', '-fxd'])
        except subprocess.CalledProcessError:
            continue

        new_lines = (
            "[![Runbot Build Status]"
            "(http://runbot.odoo-community.org/runbot/badge/flat/{0}/{1}.svg)]"
            "(http://runbot.odoo-community.org/runbot/repo/{0})\n".format(
                repo_id, version
            )
        )

        if not os.path.exists('.codeclimate.yml'):
            new_lines += (
                "[![Code Climate]"
                "(https://codeclimate.com/github/OCA/{0}/badges/gpa.svg)]"
                "(https://codeclimate.com/github/OCA/{0})\n".format(
                    repo_name
                )
            )
            shutil.copy('../.codeclimate.yml', '.')

        stuff_added = False
        for readme_line in fileinput.input('README.md', inplace=1):
            sys.stdout.write(readme_line)
            if not stuff_added and 'travis-ci.org' in readme_line:
                sys.stdout.write(new_lines)
        subprocess.check_call(['git', 'add', '--all'])
        subprocess.check_call(
            ['git', 'commit', '-m', 'add new badges and codeclimate']
        )

        # stop here!
        import pdb; pdb.set_trace()  # XXX BREAKPOINT

    os.chdir('..')
