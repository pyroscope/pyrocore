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
from collections import defaultdict

from pyrobase.parts import Bunch

from pyrocore import config
from pyrocore.util import os, pymagic
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


    def _validate_config(self):
        """ Handle and check configuration.
        """
        self.jobs = defaultdict(Bunch)

        for key, val in config.torque.items():
            # Auto-convert numbers
            if val.isdigit():
                config.torque[key] = val = int(val)

            # Assemble job parameters
            if key.startswith("job."):
                try:
                    _, name, param = key.split('.', 2)
                except (TypeError, ValueError):
                    self.fatal("Bad job configuration key %r (expecting job.NAME.PARAM)" % key)
                else:
                    self.jobs[name][param] = val


    def _add_jobs(self):
        """ Add configured jobs.
        """
        for name, params in self.jobs.items():
            for key in ("handler", "interval"):
                if key not in params:
                    self.fatal("Job '%s' is missing the required 'job.%s.%s' parameter" % (name, name, key))
    
            try:
                params.handler = pymagic.import_name(params.handler)
            except ImportError, exc:
                self.fatal("Bad handler name '%s' for job '%s'" % (params.handler, name))
            else:
                params.handler = params.handler(params)
                self.sched.add_interval_job(params.handler.run, seconds=params["interval"])


    def _run_forever(self):
        """ Run configured jobs until termination request.
        """
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                self.LOG.info("Termination request received")
                break
            else:
                # Idle work
                pass


    def mainloop(self):
        """ The main loop.
        """
        self._validate_config()

        # Set up scheduler
        from apscheduler.scheduler import Scheduler
        self.sched = Scheduler(config.torque)

        # Run scheduler
        self.sched.start()
        try:
            self._add_jobs()
            # TODO: daemonize here, or before the scheduler starts?
            self._run_forever()
        finally:
            self.sched.shutdown()


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    RtorrentQueueManager().run()


if __name__ == "__main__":
    run()

