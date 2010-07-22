# This script has to be sourced in a shell and is thus NOT executable.

# generic bootstrap
if test ! -f ../bin/activate; then
    ( cd .. && . ./bootstrap.sh )
fi
. ../bin/activate

# project
paver develop -U || return 1
paver bootstrap || return 1

