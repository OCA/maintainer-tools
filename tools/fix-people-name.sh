#!/bin/bash

# This is rough script I (Leonardo Pistone) used to fix authors and committers
# with the correct email but the name "unknown" from the
# account-analytic project.
#
# I figured that since this operation rewrites history, the migration to
# github is a good time to do that.
#
# I started only with the two *) blocks, and as soon as the "Unknown email"
# errors showed up, I added the conversion directly in the script.
#
# This can be improved and made more generic, contributions are very welcome!


filter='
  found_author=true
  found_commiter=true
  if [ "$GIT_AUTHOR_NAME" = "unknown" ]
  then
      found_author=false
      echo
      echo Gocha author $GIT_AUTHOR_EMAIL
  fi
  if [ "$GIT_COMMITTER_NAME" = "unknown" ]
  then
      found_commiter=false
      echo
      echo Gocha committer $GIT_COMMITTER_EMAIL
  fi
  '

while read someone
do
  email=$(echo $someone | awk -F"|" '{print $1;}')
  name=$(echo $someone | awk -F"|" '{print $2;}')
  filter="$filter"'

    email="'"$email"'"
    name="'"$name"'"
    if [ "$GIT_AUTHOR_NAME" = "unknown" ]; then
      is_email=$(echo $GIT_AUTHOR_EMAIL | grep "$email")
      if [ -n "$is_email" ]
      then
        export GIT_AUTHOR_NAME="$name"
        echo Author real name is $GIT_AUTHOR_NAME
        found_author=true
      fi
    fi

    if [ "$GIT_COMMITTER_NAME" = "unknown" ]; then
      is_email=$(echo $GIT_COMMITTER_EMAIL | grep "$email")
      if [ -n "$is_email" ]; then
        export GIT_COMMITTER_NAME="$name"
        echo Commiter real name is $GIT_COMMITTER_NAME
        found_commiter=true
      fi
    fi
    '
done < people-list

filter="$filter"'
    if [ "$found_author" = false ]; then
         echo "Unknown author email: $GIT_AUTHOR_EMAIL"
         exit 1
    fi
    if [ "$found_commiter" = false ]; then
         echo "Unknown committer email: $GIT_COMMITTER_EMAIL"
         exit 1
    fi
  '

git filter-branch --env-filter "$filter"
