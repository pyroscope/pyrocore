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
import shlex
import signal
import asyncore
from collections import defaultdict

from pyrobase import logutil
from pyrobase.parts import Bunch

from pyrocore import config, error
from pyrocore.util import os, pymagic, osmagic, matching
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig


def _raise_interrupt(signo, dummy):
    """ Helper for signal handling.
    """
    raise KeyboardInterrupt("Caught signal #%d" % signo)


class RtorrentQueueManager(ScriptBaseWithConfig):
    ### Keep things wrapped to fit under this comment... ##############################
    """ 
        rTorrent queue manager & daemon.
    """

    # argument description for the usage information
    ARGS_HELP = ""

    OPTIONAL_CFG_FILES = ["torque.ini"]


    def add_options(self):
        """ Add program options.
        """
        super(RtorrentQueueManager, self).add_options()

        # basic options
        self.add_bool_option("-n", "--dry-run",
            help="advise jobs not to do any real work, just tell what would happen")
        self.add_bool_option("--no-fork", "--fg", help="Don't fork into background (stay in foreground and log to console)")
        self.add_bool_option("--stop", help="Stop running daemon")
        self.add_bool_option("-?", "--status", help="Check daemon status")
        self.add_value_option("--pid-file", "PATH",
            help="file holding the process ID of the daemon, when running in background")
        self.add_value_option("--guard-file", "PATH",
            help="guard file for the process watchdog")


    def _parse_schedule(self, schedule):
        """ Parse a job schedule.
        """
        result = {}

        for param in shlex.split(str(schedule)): # do not feed unicode to shlex
            try:
                key, val = param.split('=', 1)
            except (TypeError, ValueError):
                self.fatal("Bad param '%s' in job schedule '%s'" % (param, schedule))
            else:
                result[key] = val

        return result


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

        # Validate jobs
        for name, params in self.jobs.items():
            for key in ("handler", "schedule"):
                if key not in params:
                    self.fatal("Job '%s' is missing the required 'job.%s.%s' parameter" % (name, name, key))

            bool_param = lambda key, default: matching.truth(params.get(key, default), "job.%s.%s" % (name, key))

            params.job_name = name
            params.dry_run = bool_param("dry_run", False) or self.options.dry_run
            params.active = bool_param("active", True)
            params.schedule = self._parse_schedule(params.schedule)
    
            if params.active:
                try:
                    params.handler = pymagic.import_name(params.handler)
                except ImportError, exc:
                    self.fatal("Bad handler name '%s' for job '%s':\n    %s" % (params.handler, name, exc))


    def _add_jobs(self):
        """ Add configured jobs.
        """
        for name, params in self.jobs.items():
            if params.active:
                params.handler = params.handler(params)
                self.sched.add_cron_job(params.handler.run, **params.schedule)


    def _run_forever(self):
        """ Run configured jobs until termination request.
        """
        while True:
            try:
                tick = time.time()

                asyncore.loop(timeout=1, use_poll=True)

                tick += 1.0 - time.time()
                if tick > 0:
                    time.sleep(tick)
            except KeyboardInterrupt, exc:
                self.LOG.info("Termination request received (%s)" % exc)
                break
            else:
                # Idle work
                #self.LOG.warn("IDLE %s %r" % (self.options.guard_file, os.path.exists(self.options.guard_file)))
                if self.options.guard_file and not os.path.exists(self.options.guard_file):
                    self.LOG.warn("Guard file '%s' disappeared, exiting!" % self.options.guard_file)
                    break


    def mainloop(self):
        """ The main loop.
        """
        self._validate_config()
        config.engine.load_config()

        # Defaults for process control paths
        if not self.options.no_fork and not self.options.guard_file:
            self.options.guard_file = os.path.join(config.config_dir, "run/pyrotorque") 
        if not self.options.pid_file:
            self.options.pid_file = os.path.join(config.config_dir, "run/pyrotorque.pid") 

        # Process control
        if self.options.status or self.options.stop:
            if self.options.pid_file and os.path.exists(self.options.pid_file):
                running, pid = osmagic.check_process(self.options.pid_file)
            else:
                running, pid = False, 0
    
            if self.options.stop:
                if running:
                    os.kill(pid, signal.SIGTERM)
                    self.LOG.info("Process #%d stopped." % (pid))
                elif pid:
                    self.LOG.info("Process #%d NOT running anymore." % (pid))
                else:
                    self.LOG.info("No pid file '%s'" % (self.options.pid_file or "<N/A>"))
            else:
                self.LOG.info("Process #%d %srunning." % (pid, "" if running else "NOT "))

            self.return_code = error.EX_OK if running else error.EX_UNAVAILABLE
            return

        # Check for guard file and running daemon, abort if not OK
        try:
            osmagic.guard(self.options.pid_file, self.options.guard_file)
        except EnvironmentError, exc:
            self.LOG.debug(str(exc))
            self.return_code = error.EX_TEMPFAIL 
            return

        # Detach, if not disabled via option 
        if not self.options.no_fork: # or getattr(sys.stdin, "isatty", lambda: False)():
            osmagic.daemonize(pidfile=self.options.pid_file, logfile=logutil.get_logfile())
            time.sleep(.05) # let things settle a little
        signal.signal(signal.SIGTERM, _raise_interrupt)

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

            if self.options.pid_file:
                try:
                    os.remove(self.options.pid_file)
                except EnvironmentError, exc:
                    self.LOG.warn("Failed to remove pid file '%s' (%s)" % (self.options.pid_file, exc))
                    self.return_code = error.EX_IOERR 


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup(cron_cfg="torque")
    RtorrentQueueManager().run()


if __name__ == "__main__":
    run()

