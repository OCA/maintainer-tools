#!/bin/sh

ODOO="git@github.com:/odoo/odoo.git"
OCB="git@github.com:/OCA/OCB.git"
BRANCHES="8.0 7.0"
GITDIR="/tmp/git"

if [ -f $(dirname $0)/$(basename $0).conf ]; then
    . $(dirname $0)/$(basename $0).conf
fi
if [ ! -d $GITDIR ]; then
    mkdir -p $GITDIR
fi
cd $GITDIR
if [ ! -d $(basename $OCB .git) ]; then
    git clone $OCB
    cd $(basename $OCB .git)
    git remote add odoo $ODOO
    cd ..
fi

cd $(basename $OCB .git)
git fetch --all
for BRANCH in $BRANCHES; do
    git checkout origin/$BRANCH -B $BRANCH
    git pull --ff-only
    git merge --no-edit odoo/$BRANCH || break
    git push -u origin $BRANCH
done
