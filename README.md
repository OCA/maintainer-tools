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
    $ pip install -r requirements.txt

Get a token from Github

    $ python -m tools.github_login USERNAME

Run a script

    $ python -m tools.copy_maintainers

You can use the `GITHUB_TOKEN` to specify the token

    $ GITHUB_TOKEN=xxx python -m tools.copy_maintainers
