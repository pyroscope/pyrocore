# -*- coding: utf-8 -*-
# pylint: disable=
""" Rtorrent event handler.

    Copyright (c) 2011 The PyroScope Project <pyroscope.project@gmail.com>
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
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig


class RtorrentEventHandler(ScriptBaseWithConfig):
    ### Keep things wrapped to fit under this comment... ##############################
    """
        Handle rTorrent events.
    """

    # argument description for the usage information
    ARGS_HELP = "<event> <infohash> [<args>...]"


    def add_options(self):
        """ Add program options.
        """
        super(RtorrentEventHandler, self).add_options()

        # basic options
        self.add_bool_option("--no-fork", "--fg", help="Don't fork into background (stay in foreground, default for terminal use)")


    def mainloop(self):
        """ The main loop.
        """
        # Print usage if not enough args or bad options
        if len(self.args) < 2:
            self.parser.error("No event type and info hash given!")

        if sys.stdin.isatty():
            self.options.no_fork = True

        # Need to demonize (single-fork) ouselfves here, since otherwise rTorrent dead-locks

        # TODO: Actually implement something here


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    RtorrentEventHandler().run()


if __name__ == "__main__":
    run()
