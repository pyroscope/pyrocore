# -*- coding: utf-8 -*-
# pylint: disable=I0011,C0103
""" rTorrent Disk Space House-Keeping.

    This is used in the ``rtsweep`` tool and the queue job of the
    ``pyrotoque`` daemon to free up disk space for new items, by
    deleting old items in a controlled way using a configurable order.

    Copyright (c) 2018 The PyroScope Project <pyroscope.project@gmail.com>
"""
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
from __future__ import with_statement
from __future__ import absolute_import

from pyrocore import config
from pyrocore.torrent import matching


# XXX Default sort order: loaded
# XXX check "sweep_use_builtin_rules" to filter for prio >= 0


#    test "$1" = "--aggressive" && { shift; activity=5i; } || activity=4h
#        $DRY ~/bin/rtcontrol -/1 --cull active=+$activity [ NOT [ $PROTECTED ] ] \
#            -qco loaded,size.sz,uploaded.sz,seedtime,ratio,name "$@" $INTERACTIVE; rc=$?
#   log.debug("No matches for {ruleset}

##needed=$(( $requested + $RESERVED_GiB * $GiB )) # Add a few GiB for the system
##log.info"Disk space management started [with $(print_gib $(download_free)) free]")

# Finally, go through everything sorted by age (with staged activity protection)
## -s loaded //
## --aggressive -s loaded //

#    $INFO "Disk space management finished in ${took_secs}s [$(print_gib $(download_free)) free," \
#        "$(print_gib $requested) requested]"
#        $INFO "Removed $(( $start_items - $after_items )) item(s)," \
#            "freeing $(print_gib $(( $after_free - $start_free ))) disk space" \
#            "[now $(print_gib $(download_free)) free, took ${took_secs}s]."
