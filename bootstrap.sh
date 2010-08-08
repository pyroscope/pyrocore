# This script has to be sourced in a shell and is thus NOT executable.

# generic bootstrap
if test ! -f ../bin/activate; then
    ( cd .. && . ./bootstrap.sh ) || return 1
fi
. ../bin/activate || return 1

# project
paver develop -U || return 1
paver bootstrap || return 1

