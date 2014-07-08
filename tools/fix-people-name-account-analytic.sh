#!/bin/sh

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


git filter-branch --env-filter  '
if [ "$GIT_AUTHOR_NAME" = "unknown" ]
then
  case "$GIT_AUTHOR_EMAIL" in
    "laetitia.gangloff@acsone.eu")
      export GIT_AUTHOR_NAME="Laetitia Gangloff"
      ;;
    "vincent.renaville@camptocamp.com")
      export GIT_AUTHOR_NAME="Vincent Renaville"
      ;;
    "markus.schneider@initos.com")
      export GIT_AUTHOR_NAME="Markus Schneider"
      ;;
    "pedro.baeza@serviciosbaeza.com")
      export GIT_AUTHOR_NAME="Pedro M. Baeza"
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
