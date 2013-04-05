# This script has to be sourced in a shell and is thus NOT executable.
#
# Copyright (c) 2010-2013 The PyroScope Project <pyroscope.project@gmail.com>
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
. ../util.sh

# generic bootstrap
test -f ../bin/activate || ( cd .. && . ./bootstrap.sh ) || abend "top-level bootstrap failed"
. ../bin/activate || abend "venv activate failed"

# essential tools
test -x ../bin/paver || pip_install -U "paver>=1.0.1"

# package dependencies (optional)
for pkgreq in "Tempita>=0.5.1" "APScheduler>=2.0.2"; do
    pip_install_opt "$pkgreq"
done

# git dependencies
for project in $git_projects; do
    test ! -d ../$project || ( cd ../$project && $PWD/../bin/paver -q develop -U)
done

# project
../bin/paver -q develop -U || abend "installing $(basename $(pwd)) into venv failed"
../bin/paver bootstrap || abend "bootstrapping $(basename $(pwd)) failed"

