# -*- coding: utf-8 -*-
# pylint: disable=I0011
""" rTorrent Watch Jobs.

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
from __future__ import with_statement

import sys
import logging
import asyncore

from pyrobase.parts import Bunch
from pyrocore import error, config
from pyrocore.util import os, xmlrpc, pymagic
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig

try: 
    import pyinotify
except ImportError, exc:
    pyinotify = Bunch(WatchManager=None, ProcessEvent=object)


class RemoteWatch(object):
    """ rTorrent remote torrent file watch.
    """

    def __init__(self, config=None):
        """ Set up remote watcher.
        """
        self.config = config or {}
        self.LOG = pymagic.get_class_logger(self)
        self.LOG.info("Remote watcher created with config %r" % self.config)


    def run(self):
        """ Check remote watch target.
        """
        # TODO: ftp. ssh, and remote rTorrent instance (extra view?) as sources!
        # config: 
        #   local_dir   storage path (default local sessiondir + '/remote-watch-' + jobname
        #   target      URL of target to watch


class TreeWatchHandler(pyinotify.ProcessEvent):
    """ inotify event handler for rTorrent folder tree watch.
    
        See https://github.com/seb-m/pyinotify/.
    """

    def my_init(self, **kw):
        self.job = kw["job"]
        

    def process_IN_CLOSE_WRITE(self, event):
        """ File written.
        """
        # <Event dir=False name=xx path=/var/torrent/watch/tmp pathname=/var/torrent/watch/tmp/xx>
        if not event.dir:
            self.job.LOG.info("File %r written" % event.pathname)


    def process_IN_MOVED_TO(self, event):
        """ File moved into tree.
        """
        # <Event dir=False name=yy path=/var/torrent/watch/tmp pathname=/var/torrent/watch/tmp/yy>
        if not event.dir:
            self.job.LOG.info("File %r moved here" % event.pathname)


    def process_default(self, event):
        """ Fallback.
        """
        self.job.LOG.warning("Unexpected inotify event %r" % event)


class TreeWatch(object):
    """ rTorrent folder tree watch via inotify.
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.LOG = pymagic.get_class_logger(self)
        self.LOG.info("Tree watcher created with config %r" % self.config)

        self.manager = None
        self.handler = None
        self.notifier = None

        if not self.config.path:
            raise error.UserError("You nedd to set 'job.%s.path' in the condfiguration!" % self.config.job_name)

        self.config.path = os.path.abspath(os.path.expanduser(self.config.path.rstrip(os.sep)))
        if not os.path.isdir(self.config.path):
            raise error.UserError("Path '%s' is not a directory!" % self.config.path)
        
        if self.config.active:
            self.setup()

        
    def setup(self):
        """ Set up inotify manager.
        
            See https://github.com/seb-m/pyinotify/.
        """
        if not pyinotify.WatchManager:
            raise error.UserError("You need to install 'pyinotify' to use %s!" % (
                self.__class__.__name__))

        self.manager = pyinotify.WatchManager()
        self.handler = TreeWatchHandler(job=self)
        self.notifier = pyinotify.AsyncNotifier(self.manager, self.handler)

        mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO
        self.manager.add_watch(self.config.path, mask, rec=True)


    def run(self):
        """ We don't really need any timed scheduling.
        """
        # TODO: Maybe do some stats logging here, once per hour or so
        # XXX: We can handle files that were not valid bencode here, from a Queue! And watch.ini reloading.


class TreeWatchCommand(ScriptBaseWithConfig):
    ### Keep things wrapped to fit under this comment... ##############################
    """ Use tree watcher directly from cmd line (python -m pyrocore.torrent.watch <DIR>)
    """

    # log level for user-visible standard logging
    STD_LOG_LEVEL = logging.DEBUG

    # argument description for the usage information
    ARGS_HELP = "<directory>"


    def mainloop(self):
        """ The main loop.
        """
        # Print usage if not enough args or bad options
        if len(self.args) < 1:
            self.parser.error("No method given!")

        watch = TreeWatch(Bunch(path = self.args[0], active = False, dry_run=True))
        watch.setup()
        asyncore.loop(timeout=~0, use_poll=True)


    @classmethod
    def main(cls): #pragma: no cover
        """ The entry point.
        """
        ScriptBase.setup()
        cls().run()


if __name__ == "__main__":
    TreeWatchCommand.main()

