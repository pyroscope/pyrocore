# This script has to be sourced in a shell and is thus NOT executable.
#
# Copyright (c) 2010 The PyroScope Project <pyroscope.project@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

git_projects="pyrobase auvyon"
set +e

fail() {
    echo
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo -n >&2 "ERROR: "
    for i in "$@"; do
        echo >&2 "$i"
    done
    #set +e
    return 1
}

# generic bootstrap
if test ! -f ../bin/activate; then
    ( cd .. && . ./bootstrap.sh ) || fail "top-level bootstrap failed"
fi
. ../bin/activate || fail "venv activate failed"
test -x ../bin/pip || ../bin/easy_install pip
test -x ../bin/pip || ln -s $(cd ../bin && ls -1 pip-* | tail -n1) ../bin/pip
test -x ../bin/pip || fail "Installation of pip to ../bin failed somehow" "pwd=$(pwd)"

# essential tools
test -x ../bin/paver || ../bin/pip install -U "paver>=1.0.1" || fail "paver install failed"

# package dependencies (optional)
for pkgreq in "Tempita>=0.5.1" "APScheduler>=2.0.2"; do
    ../bin/pip install "$pkgreq"
done

# git dependencies
for project in $git_projects; do
    test ! -d ../$project || ( cd ../$project && $PWD/../bin/paver -q develop -U)
done

# project
../bin/paver -q develop -U || fail "installing $(basename $(pwd)) into venv failed"
../bin/paver bootstrap || fail "bootstrapping $(basename $(pwd)) failed"

set +e
