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

export DEBFULLNAME=pyroscope
export DEBEMAIL=pyroscope.project@gmail.com

deactivate 2>/dev/null
test -z "$PYTHON" -a -x "/usr/bin/python2" && PYTHON="/usr/bin/python2"
test -z "$PYTHON" -a -x "/usr/bin/python" && PYTHON="/usr/bin/python"
test -z "$PYTHON" && PYTHON="python"

git_projects="pyrobase auvyon"
. ./util.sh # load funcs

# generic bootstrap
test -f ./bin/activate || install_venv --no-site-packages
. ./bin/activate || abend "venv activate failed"

grep DEBFULLNAME bin/activate >/dev/null || cat >>bin/activate <<EOF
export DEBFULLNAME=$DEBFULLNAME
export DEBEMAIL=$DEBEMAIL
EOF

# tools
pip_install -U "setuptools>=0.6c11"
pip_install -U "paver>=1.0.5"
##pip_install -U "nose>=1.0"
##pip_install -U "coverage>=3.4"
pip_install -U "yolk3k"
##pip_install -U "PasteScript>=1.7.3"

# Harmless options (just install them, but ignore errors)
pip_install_opt -U "Tempita>=0.5.1"
pip_install_opt -U "APScheduler>=2.0.2"
pip_install_opt -U "waitress>=0.8.2"
pip_install_opt -U "WebOb>=1.2.3"
##pip_install_opt -U "psutil>=0.6.1"

# pyrobase
test ! -d pyrobase || ( builtin cd pyrobase && ../bin/paver -q develop -U)

# essential tools
test -x ./bin/paver || pip_install -U "paver>=1.0.1"

# package dependencies (optional)
for pkgreq in "Tempita>=0.5.1" "APScheduler>=2.0.2"; do
    pip_install_opt "$pkgreq"
done

# git dependencies
for project in $git_projects; do
    test ! -d ../$project || ( builtin cd ../$project && $PWD/bin/paver -q develop -U)
done

# project
./bin/paver -q develop -U || abend "installing $(basename $(pwd)) into venv failed"
./bin/paver bootstrap || abend "bootstrapping $(basename $(pwd)) failed"
