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

# generic bootstrap
if test ! -f ../bin/activate; then
    ( cd .. && . ./bootstrap.sh ) || return 1
fi
. ../bin/activate || return 1

# essential tools
test -x ../bin/paver || ../bin/easy_install -U "paver>=1.0.1" || return 1

# pyrobase
test ! -d ../pyrobase || ( cd ../pyrobase && $PWD/../bin/paver develop -U)

# project
../bin/paver develop -U || return 1
../bin/paver bootstrap || return 1

