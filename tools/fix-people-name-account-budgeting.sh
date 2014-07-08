#!/bin/sh

# This is rough script I (Leonardo Pistone) used to fix authors and committers
# with the correct email but the name "unknown" from the
# account-budgeting project.
#
# I figured that since this operation rewrites history, the migration to 
# github is a good time to do that.
#
# I started only with the two *) blocks, and as soon as the "Unknown email"
# errors showed up, I added the conversion directly in the script.
# 
# This can be improved and made more generic, contributions are very welcome!


git filter-branch --env-filter  '
if [ "$GIT_AUTHOR_NAME" = "unknown" ]
then
  case "$GIT_AUTHOR_EMAIL" in
    "frederic.clementi@camptocamp.com") 
      export GIT_AUTHOR_NAME="Frederic Clementi"
      ;;
    "nicolas.bessi@camptocamp.com") 
      export GIT_AUTHOR_NAME="Nicolas Bessi"
      ;;
    "alexandre.fayolle@camptocamp.com") 
      export GIT_AUTHOR_NAME="Alexandre Fayolle"
      ;;
    "vincent.renaville@camptocamp.com") 
      export GIT_AUTHOR_NAME="Vincent Renaville"
      ;;
    *) 
      echo "Unknown author email: $GIT_AUTHOR_EMAIL"
      exit 1
      ;;
  esac
  echo
  echo Gocha author $GIT_AUTHOR_EMAIL
  echo His real name is $GIT_AUTHOR_NAME
fi

if [ "$GIT_COMMITTER_NAME" = "unknown" ]
then
  case "$GIT_COMMITTER_EMAIL" in
    "nicolas.bessi@camptocamp.com") 
      export GIT_COMMITTER_NAME="Nicolas Bessi"
      ;;
    "vincent.renaville@camptocamp.com") 
      export GIT_COMMITTER_NAME="Vincent Renaville"
      ;;
    "alexandre.fayolle@camptocamp.com") 
      export GIT_COMMITTER_NAME="Alexandre Fayolle"
      ;;
    *) 
      echo "Unknown committer email: $GIT_COMMITTER_EMAIL"
      exit 1
      ;;
  esac
  echo
  echo Gocha committer $GIT_COMMITTER_EMAIL
  echo His real name is $GIT_COMMITTER_NAME
fi
'
