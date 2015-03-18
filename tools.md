# OCA Maintainers Tools

## Installation

    $ git clone git@github.com:OCA/maintainers-tools.git
    $ cd maintainers-tools
    $ virtualenv env
    $ . env/bin/activate
    $ python setup.py install

If you want to use the `oca-copy-branches` command, you also have to install:
https://github.com/felipec/git-remote-bzr. `git-remote-bzr` must be in the
`$PATH`.

## Usage

Get a token from Github, you may have to delete the existing one from Account settings -> Applications -> Personnal Access Token

    $ oca-github-login USERNAME

**Copy the users from the maintainers team to the other teams**

    $ oca-copy-maintainers

**Migrate the Launchpad branches to GitHub**

The mapping of the branches is in `tools/branches.yaml`.
When running:

    $ oca-copy-branches PATH

all the Launchpad branches will be fetched (as `git` repositories with `git-remote-bzr` in `PATH`).
The default mode of execution is a `dry run` mode, it will not push the branches to GitHub.
If you want to push the branches to GitHub, run:

    $ oca-copy-branches PATH --push

To copy the branches of a particular project, put the name of the project (the GitHub's one):

    $ oca-copy-branches PATH --projects OCA/magento-connector

The same tool can also be used to move other branches to GitHub, see
https://github.com/OCA/maintainers-tools/wiki/How-to-move-a-Merge-Proposal-to-GitHub

**Set labels on OCA repository on GitHub**

Set standardized labels to ease the issue workflow on all repositories with same colors
This tools will also warn you what are the specific labels on some repository

    $ oca-set-repo-labels

## Developers

As a developer, you want to launch the scripts without installing the
egg. 

    $ git clone git@github.com:OCA/maintainers-tools.git
    $ virtualenv env
    $ . env/bin/activate
    $ pip install -e maintainers-tools

**Get a token from Github**

    $ python -m tools.github_login USERNAME

**Run a script**

    $ python -m tools.copy_maintainers

You can use the `GITHUB_TOKEN` environment variable to specify the token

    $ GITHUB_TOKEN=xxx python -m tools.copy_maintainers
