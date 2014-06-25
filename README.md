# OCA Maintainers Tools

## Installation

    $ git clone git@github.com:OCA/maintainers-tools.git
    $ virtualenv env
    $ . env/bin/activate
    $ python setup.py install

## Usage

**Get a token from Github**

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

    $ oca-copy-branches PATH --projects magento-connector

## Developers

As a developer, you want to launch the scripts without installing the
egg. 

    $ git clone git@github.com:OCA/maintainers-tools.git
    $ virtualenv env
    $ . env/bin/activate
    $ python setup.py develop

**Get a token from Github**

    $ python -m tools.github_login USERNAME

**Run a script**

    $ python -m tools.copy_maintainers

You can use the `GITHUB_TOKEN` environment variable to specify the token

    $ GITHUB_TOKEN=xxx python -m tools.copy_maintainers
