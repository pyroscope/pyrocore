# This script has to be sourced in a shell and is thus NOT executable.

# generic bootstrap
if test ! -f ../bin/activate; then
    ( cd .. && . ./bootstrap.sh ) || return 1
fi
. ../bin/activate || return 1

# essential tools
which paver >/dev/null || easy_install -U "paver>=1.0.1" || return 1

# pyrobase
test ! -d ../pyrobase || ( cd ../pyrobase && paver develop -U)

# project
paver develop -U || return 1
paver bootstrap || return 1

