# This script has to be sourced in a shell and is thus NOT executable.

# generic bootstrap
if test ! -f ../bin/activate; then
    ( cd .. && . ./bootstrap.sh )
else
    . ../bin/activate
fi

# project
paver develop -U || return 1
paver bootstrap || return 1

