OCA Maintainers Tools
=====================

Installation
------------

    $ git clone git@github.com:OCA/maintainers-tools.git
    $ virtualenv env
    $ . env/bin/activate
    $ python setup.py install

Usage
-----

Get a token from Github

    $ oca-github-login USERNAME

Copy the users from the maintainers team to the other teams

    $ oca-copy-maintainers
