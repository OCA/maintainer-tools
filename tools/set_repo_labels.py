# -*- coding: utf-8 -*-
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
"""
Create and modify labels on github to have same labels and same color
on all repo
"""
from __future__ import print_function
from .github_login import login

REPO_TO_IGNORE = [
    ".github",
    "mirrors-flake8",
]

# List of labels to sync on all repositories
# {name: (color, description)}
ALL_LABELS = {
    "bug": ("fc2929", None),
    "duplicate": ("cccccc", None),
    "enhancement": ("84b6eb", None),
    "help wanted": ("159818", None),
    "invalid": ("e6e6e6", None),
    "question": ("cc317c", None),
    "needs fixing": ("eb6420", None),
    "needs review": ("fbca04", None),
    "needs more information": ("eb6420", None),
    "approved": ("045509", None),
    "work in progress": ("0052cc", None),
    "wontfix": ("ffffff", None),
    "migration": ("d4c5f9", None),
    "ready to merge": ("bfdadc", None),
    # Labels related to actions/stale github workflow
    "no stale": (
        "524D44",
        "Use this label to prevent the automated stale action "
        "from closing this PR/Issue.",
    ),
    "stale": (
        "006B75",
        "PR/Issue without recent activity, it'll be soon closed automatically.",
    ),
}


def main():
    gh = login()
    for repo in gh.repositories_by("OCA"):
        if repo.name in REPO_TO_IGNORE:
            continue
        repo_labels = {label.name.lower(): label for label in repo.labels()}
        target_labels = set(ALL_LABELS.keys())
        existing_labels = set(repo_labels.keys())
        labels_to_update = target_labels & existing_labels
        labels_to_create = target_labels - existing_labels
        # Report if extra labels are found, nothing to do though
        extra_labels = existing_labels - target_labels
        for label_name in extra_labels:
            print(f"Found extra label '{repo_labels[label_name].name}' in {repo.name}")
        # Check existing labels
        for label_name in labels_to_update:
            label_color, label_description = ALL_LABELS[label_name]
            repo_label = repo_labels[label_name]
            if (
                repo_label.name != label_name
                or repo_label.color != label_color
                or (
                    label_description is not None
                    and repo_label.description != label_description
                )
            ):
                print(
                    f"Updating label '{repo_label.name}' -> '{label_name}', "
                    f"'{repo_label.color}' -> '{label_color}', "
                    f"'{repo_label.description}' -> '{label_description}' "
                    f"in {repo.name}"
                )
                repo_label.update(label_name, label_color, label_description)
        # Create labels
        for label_name in labels_to_create:
            label_color, label_description = ALL_LABELS[label_name]
            print(f"Creating label '{label_name}' in {repo.name}")
            repo.create_label(label_name, label_color, label_description)


if __name__ == "__main__":
    main()
