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
from pyrocore import error
from pyrocore import config as configuration
from pyrocore.util import os, fmt, xmlrpc, pymagic, metafile
from pyrocore.torrent import matching
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
        self.LOG.debug("Remote watcher created with config %r" % self.config)


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
    
    METAFILE_EXT = (".torrent", ".load", ".start", ".queue")
    

    def my_init(self, **kw):
        self.job = kw["job"]
        

    def handle_metafile(self, pathname):
        """ Handle a new metafile.
        """
        try:
            data = metafile.checked_open(pathname)
        except EnvironmentError, exc:
            self.error("Can't read metafile '%s' (%s)" % (
                pathname, str(exc).replace(": '%s'" % pathname, ""),
            ))
            return
        except ValueError, exc:
            self.job.LOG.error("Invalid metafile '%s': %s" % (pathname, exc))
            return
 
        info_hash = metafile.info_hash(data)
        self.job.LOG.info("Loaded '%s' from metafile '%s'" % (data["info"]["name"], pathname))
        
        # Check whether item is already loaded
        try:
            name = self.job.proxy.d.get_name(info_hash, fail_silently=True)
        except xmlrpc.ERRORS, exc:
            if exc.faultString != "Could not find info-hash.":
                self.job.LOG.error("While checking for #%s: %s" % (info_hash, exc))
                return
        else:
            self.job.LOG.warn("Item #%s '%s' already added to client" % (info_hash, name))
            return

        # TODO: dry_run
        try:
            # TODO: Scrub metafile if requested

            # Build indicator flags for target state from filename
            flags = pathname.split(os.sep)
            flags.extend(flags[-1].split('.'))
            flags = set(flags)

            # Determine target state
            start_it = self.job.config.load_mode in ("start",)
            queue_it = self.job.config.queued 

            if "start" in flags:
                start_it = True
            elif "load" in flags:
                start_it = False

            if "queue" in flags:
                queue_it = True

            # Load metafile into client
            if queue_it:
                commands = () if start_it else ("d.set_priority=0",)
            else:
                commands = ("d.start=",) if start_it else ()
            self.job.proxy.load_verbose(pathname, *commands)
            msg = "%s: Loaded '%s' from '%s/'" % (
                self.__class__.__name__,
                fmt.to_utf8(self.job.proxy.d.get_name(info_hash, fail_silently=True)),
                os.path.dirname(pathname).rstrip(os.sep),
            )
            self.job.proxy.log('', msg)

            # TODO: Evaluate fields and set client values
            # TODO: Add metadata to tied file if requested

        except xmlrpc.ERRORS, exc:
            self.job.LOG.error("While loading #%s: %s" % (info_hash, exc))


    def handle_path(self, event):
        """ Handle a path-related event.
        """
        self.job.LOG.debug("Notification %r" % event)
        if event.dir:
            return
        
        if any(event.pathname.endswith(i) for i in self.METAFILE_EXT):
            self.handle_metafile(event.pathname)
        elif os.path.basename(event.pathname) == "watch.ini":
            self.job.LOG.info("Reloading watch config for '%s'" % event.path)
            # TODO: Load new metadata


    def process_IN_CLOSE_WRITE(self, event):
        """ File written.
        """
        # <Event dir=False name=xx path=/var/torrent/watch/tmp pathname=/var/torrent/watch/tmp/xx>
        self.handle_path(event)


    def process_IN_MOVED_TO(self, event):
        """ File moved into tree.
        """
        # <Event dir=False name=yy path=/var/torrent/watch/tmp pathname=/var/torrent/watch/tmp/yy>
        self.handle_path(event)


    def process_default(self, event):
        """ Fallback.
        """
        if self.LOG.isEnabledFor(logging.DEBUG):
            self.job.LOG.debug("Ignored inotify event:\n    %r" % event)
        else:
            self.job.LOG.warning("Unexpected inotify event %r" % event)


class TreeWatch(object):
    """ rTorrent folder tree watch via inotify.
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.LOG = pymagic.get_class_logger(self)
        self.LOG.debug("Tree watcher created with config %r" % self.config)

        self.manager = None
        self.handler = None
        self.notifier = None

        bool_param = lambda key, default: matching.truth(self.config.get(key, default), "job.%s.%s" % (self.config.job_name, key))

        if not self.config.path:
            raise error.UserError("You need to set 'job.%s.path' in the configuration!" % self.config.job_name)

        self.config.queued = bool_param("queued", False)

        self.config.path = set([os.path.abspath(os.path.expanduser(path.strip()).rstrip(os.sep))
            for path in self.config.path.split(os.pathsep)
        ])
        for path in self.config.path:
            if not os.path.isdir(path):
                raise error.UserError("Path '%s' is not a directory!" % path)

        # Get client proxy
        self.proxy = xmlrpc.RTorrentProxy(configuration.scgi_url)
        self.proxy._set_mappings()
        
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

        if self.LOG.isEnabledFor(logging.DEBUG):
            mask = pyinotify.ALL_EVENTS
        else:
            mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO

        # Add all configured base dirs
        for path in self.config.path:
            self.manager.add_watch(path.strip(), mask, rec=True, auto_add=True)


    def run(self):
        """ We don't really need any timed scheduling.
        """
        # TODO: Maybe do some stats logging here, once per hour or so
        # TODO: We can handle files that were not valid bencode here, from a Queue! And watch.ini reloading.

        # XXX: Add a check that the notifier is working, by creating / deleting a file
        # XXX: Also check for unhandled files

        # TODO: XXX: Esepcially on startup, we need to walk the directory tree
        #    and check for files not loaded (by checking hashes)!
        #    Or maybe rename them during loading?! Makes detection easy.


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
            self.parser.error("You have to provide the root directory of your watch tree!")

        configuration.engine.load_config()
        watch = TreeWatch(Bunch(path=self.args[0], active=True, dry_run=True, load_mode=None))
        asyncore.loop(timeout=~0, use_poll=True)


    @classmethod
    def main(cls): #pragma: no cover
        """ The entry point.
        """
        ScriptBase.setup()
        cls().run()


if __name__ == "__main__":
    TreeWatchCommand.main()

