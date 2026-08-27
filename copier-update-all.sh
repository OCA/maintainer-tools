#!/bin/bash

# This is script is meant to run in the image built from this repository.

set -eauxo pipefail

REPOS=:all:

gh auth login --hostname=github.com --git-protocol=https --web

gh auth setup-git

function install-pre-commit {
  rm -fr /tmp/pre-commit-env /usr/local/bin/pre-commit
  python3 -m venv /tmp/pre-commit-env
  /tmp/pre-commit-env/bin/pip install pre-commit
  ln -s /tmp/pre-commit-env/bin/pre-commit /usr/local/bin/pre-commit
}

mise use -g python@3.6
install-pre-commit
oca-copier-update \
  --repos $REPOS \
  --branches 12.0 \
  --git-protocol https

mise use -g python@3.8
install-pre-commit
oca-copier-update \
  --repos $REPOS \
  --branches 13.0 \
  --git-protocol https

mise use -g python@3.11
install-pre-commit
oca-copier-update \
  --repos $REPOS \
  --branches 14.0,15.0,16.0,17.0,18.0 \
  --git-protocol https
