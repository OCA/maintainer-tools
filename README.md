[![Build Status](https://travis-ci.org/OCA/maintainers-tools.svg?branch=master)](https://travis-ci.org/OCA/maintainers-tools)
[![Coverage Status](https://img.shields.io/coveralls/OCA/maintainers-tools.svg)](https://coveralls.io/r/OCA/maintainers-tools?branch=master)

# OCA Maintainers Tools

## Installation

    $ git clone git@github.com:OCA/maintainers-tools.git
    $ virtualenv env
    $ . env/bin/activate
    $ python setup.py install

## Usage

Get a token from Github

    $ oca-github-login USERNAME

Copy the users from the maintainers team to the other teams

    $ oca-copy-maintainers

## Developers

As a developer, you want to launch the scripts without installing the
egg. 

    $ git clone git@github.com:OCA/maintainers-tools.git
    $ virtualenv env
    $ . env/bin/activate
    $ python setup.py develop

Get a token from Github

    $ python -m tools.github_login USERNAME

Run a script

    $ python -m tools.copy_maintainers

You can use the `GITHUB_TOKEN` environment variable to specify the token

    $ GITHUB_TOKEN=xxx python -m tools.copy_maintainers
