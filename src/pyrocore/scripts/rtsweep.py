# -*- coding: utf-8 -*-
# pylint: disable=
""" Rtorrent disk space management.

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
from __future__ import absolute_import

import sys

from pyrocore import config
from pyrocore.torrent import broom
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig


class RtorrentSweep(ScriptBaseWithConfig):
    ### Keep things wrapped to fit under this comment... ##############################
    """
        Manage disk space by deleting items loaded into rTorrent, including their data,
        following configured rules that define an order of what to remove first.

        The required space is passed as the first argument, either in bytes or
        qualified with a unit character (K=KiB, M=MiB, G=GiB). Alternatively, you can
        pass a metafile path, with the requirement calculated from its content size.

        Use "show" instead to list the active rules, ordered by their priority.
    """

    # argument description for the usage information
    ARGS_HELP = "<space requirement>|SHOW"


    def add_options(self):
        """ Add program options.
        """
        super(RtorrentSweep, self).add_options()

        # basic options
        self.add_bool_option("-n", "--dry-run",
            help="do not remove anything, just tell what would happen")
        self.add_value_option("-p", "--path", "PATH",
            help="path into the filesystem to sweep (else the default download location)")
        self.add_value_option("-r", "--rules", "RULESET [-r ...]",
            action="append", default=[],
            help="name the ruleset(s) to use, instead of the default ones")


    def mainloop(self):
        """ The main loop.
        """
        # Print usage if not enough args or bad options
        if len(self.args) < 1:
            self.parser.error("No space requirement provided!")

        # XXX: Ensure a lock file or similar is checked here,
        #      to avoid / delay concurrent execution

        # TODO: Actually implement something here


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    RtorrentSweep().run()


if __name__ == "__main__":
    run()
