# This script has to be sourced in a shell and is thus NOT executable.

# generic bootstrap
. ../bootstrap.sh

# project
paver develop -U || return 1
paver bootstrap || return 1

