# -*- coding: utf-8 -*-
"""
Create and modify labels on github to have same labels and same color
on all repo
"""
from .github_login import login

REPO_TO_IGNORE = [
    'odoo-community.org',
    'community-data-files',
    'contribute-md-template',
    'website',
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
    'work in progress': '0052cc',
    'wontfix': 'ffffff',
    }


def main():
    gh = login()

    all_repos = gh.iter_user_repos('OCA')

    for repo in all_repos:
        if repo.name in REPO_TO_IGNORE:
            continue
        labels = repo.iter_labels()

        existing_labels = dict((l.name.lower(), l.color) for l in labels)

        to_create = []
        to_change_color = []
        for needed_label in all_labels:
            if needed_label not in existing_labels.keys():
                to_create.append(needed_label)
            elif existing_labels[needed_label] != all_labels[needed_label]:
                to_change_color.append(needed_label)

        extra_labels = [l for l in existing_labels if l not in all_labels]

        if to_create:
            print ('Repo %s - Create %s missing labels'
                   % (repo.name, len(to_create)))

            for label_name in to_create:
                success = repo.create_label(label_name, all_labels[label_name])
                if not success:
                    print ("Failed to create a label on '%s'!"
                           " Please check you access right to this repository."
                           % repo.name)

        if to_change_color:
            print ('Repo %s - Update %s labels with wrong color'
                   % (repo.name, len(to_change_color)))

            for label_name in to_change_color:
                success = repo.update_label(label_name, all_labels[label_name])
                if not success:
                    print ("Failed to update a label on '%s'!"
                           " Please check you access right to this repository."
                           % repo.name)

        if extra_labels:
            print ('Repo %s - Found %s extra labels'
                   % (repo.name, len(extra_labels)))
            for label_name in extra_labels:
                print label_name


if __name__ == '__main__':
    main()
