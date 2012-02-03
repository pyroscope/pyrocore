""" rTorrent queue manager & daemon.

    Copyright (c) 2012 The PyroScope Project <pyroscope.project@gmail.com>
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
import sys
import time

from pyrocore import config
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig


class RtorrentQueueManager(ScriptBaseWithConfig):
    ### Keep things wrapped to fit under this comment... ##############################
    """ 
        rTorrent queue manager & daemon.
    """

    # argument description for the usage information
    ARGS_HELP = ""


    def add_options(self):
        """ Add program options.
        """
        super(RtorrentQueueManager, self).add_options()

        # basic options
        self.add_bool_option("--no-fork", "--fg", help="Don't fork into background (stay in foreground and log to console)")


    def mainloop(self):
        """ The main loop.
        """
        # Set up scheduler
        from apscheduler.scheduler import Scheduler
        sched = Scheduler()

        # Add configured tasks

        # Start scheduler
        sched.start()
        try:
            while True:
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    self.LOG.info("Termination request received")
                    break
                else:
                    # Idle work
                    pass
        finally:
            sched.shutdown()


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    RtorrentQueueManager().run()


if __name__ == "__main__":
    run()

