# -*- coding: utf-8 -*-
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
"""
Create and modify labels on github to have same labels and same color
on all repo
"""
from __future__ import print_function
from .github_login import login

REPO_TO_IGNORE = [
]

# here is the list of labels we need in each repo
all_labels = {
    'bug': 'fc2929',
    'duplicate': 'cccccc',
    'enhancement': '84b6eb',
    'help wanted': '159818',
    'invalid': 'e6e6e6',
    'question': 'cc317c',
    'needs fixing': 'eb6420',
    'needs review': 'fbca04',
    'approved': '045509',
    'work in progress': '0052cc',
    'wontfix': 'ffffff',
    'migration': 'd4c5f9',
    'ready to merge': 'bfdadc',
}


def main():
    gh = login()

    all_repos = gh.repositories_by('OCA')

    for repo in all_repos:
        if repo.name in REPO_TO_IGNORE:
            continue
        wanted_labels = all_labels.copy()
        for label in repo.labels():
            if label.name.lower() in wanted_labels:
                wanted_name = label.name.lower()
                wanted_color = wanted_labels[label.name.lower()]
                if label.name != wanted_name or label.color != wanted_color:
                    print(
                        "fixing name/color of label",
                        label.name,
                        "in",
                        repo.name,
                    )
                    label.update(wanted_name, wanted_color)
                wanted_labels.pop(label.name.lower())
            else:
                print("found extra label", label.name, "in", repo.name)
        for name, color in wanted_labels.items():
            print("adding label", name, "in", repo.name)
            repo.create_label(name, color)


if __name__ == '__main__':
    main()
