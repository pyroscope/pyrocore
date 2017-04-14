# -*- coding: utf-8 -*-
# pylint: disable=I0011,C0103
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
from __future__ import absolute_import

# TODO: Re-tie metafiles when they're moved in the tree

import time
import logging
import asyncore

from pyrobase import logutil
from pyrobase.parts import Bunch
from pyrocore import error
from pyrocore import config as configuration
from pyrocore.util import os, fmt, xmlrpc, pymagic, metafile, traits
from pyrocore.torrent import matching, formatting
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig

try:
    import pyinotify
except ImportError as exc:
    pyinotify = Bunch(WatchManager=None, ProcessEvent=object, _import_error=str(exc)) # bogus pylint: disable=C0103


class MetafileHandler(object):
    """ Handler for loading metafiles into rTorrent.
    """

    def __init__(self, job, pathname):
        """ Create a metafile handler.
        """
        self.job = job
        self.metadata = None
        self.ns = Bunch(
            pathname=os.path.abspath(pathname),
            info_hash=None,
            tracker_alias=None,
        )


    def parse(self):
        """ Parse metafile and check pre-conditions.
        """
        try:
            if not os.path.getsize(self.ns.pathname):
                # Ignore 0-byte dummy files (Firefox creates these while downloading)
                self.job.LOG.warn("Ignoring 0-byte metafile '%s'" % (self.ns.pathname,))
                return
            self.metadata = metafile.checked_open(self.ns.pathname)
        except EnvironmentError as exc:
            self.job.LOG.error("Can't read metafile '%s' (%s)" % (
                self.ns.pathname, str(exc).replace(": '%s'" % self.ns.pathname, ""),
            ))
            return
        except ValueError as exc:
            self.job.LOG.error("Invalid metafile '%s': %s" % (self.ns.pathname, exc))
            return

        self.ns.info_hash = metafile.info_hash(self.metadata)
        self.ns.info_name = self.metadata["info"]["name"]
        self.job.LOG.info("Loaded '%s' from metafile '%s'" % (self.ns.info_name, self.ns.pathname))

        # Check whether item is already loaded
        try:
            name = self.job.proxy.d.name(self.ns.info_hash, fail_silently=True)
        except xmlrpc.HashNotFound:
            pass
        except xmlrpc.ERRORS as exc:
            if exc.faultString != "Could not find info-hash.":
                self.job.LOG.error("While checking for #%s: %s" % (self.ns.info_hash, exc))
                return
        else:
            self.job.LOG.warn("Item #%s '%s' already added to client" % (self.ns.info_hash, name))
            return

        return True


    def addinfo(self):
        """ Add known facts to templating namespace.
        """
        # Basic values
        self.ns.watch_path = self.job.config.path
        self.ns.relpath = None
        for watch in self.job.config.path:
            if self.ns.pathname.startswith(watch.rstrip('/') + '/'):
                self.ns.relpath = os.path.dirname(self.ns.pathname)[len(watch.rstrip('/'))+1:]
                break

        # Build indicator flags for target state from filename
        flags = self.ns.pathname.split(os.sep)
        flags.extend(flags[-1].split('.'))
        self.ns.flags = set(i for i in flags if i)

        # Metafile stuff
        announce = self.metadata.get("announce", None)
        if announce:
            self.ns.tracker_alias = configuration.map_announce2alias(announce)

        main_file = self.ns.info_name
        if "files" in self.metadata["info"]:
            main_file = list(sorted((i["length"], i["path"][-1])
                for i in self.metadata["info"]["files"]))[-1][1]
        self.ns.filetype = os.path.splitext(main_file)[1]

        # Add name traits
        kind, info = traits.name_trait(self.ns.info_name, add_info=True)
        self.ns.traits = Bunch(info)
        self.ns.traits.kind = kind
        self.ns.label = '/'.join(traits.detect_traits(
            name=self.ns.info_name, alias=self.ns.tracker_alias, filetype=self.ns.filetype)).strip('/')

        # Finally, expand commands from templates
        self.ns.commands = []
        for key, cmd in sorted(self.job.custom_cmds.items()):
            try:
                self.ns.commands.append(formatting.expand_template(cmd, self.ns))
            except error.LoggableError as exc:
                self.job.LOG.error("While expanding '%s' custom command: %s" % (key, exc))


    def load(self):
        """ Load metafile into client.
        """
        if not self.ns.info_hash and not self.parse():
            return

        self.addinfo()

        # TODO: dry_run
        try:
            # TODO: Scrub metafile if requested

            # Determine target state
            start_it = self.job.config.load_mode.lower() in ("start", "started")
            queue_it = self.job.config.queued

            if "start" in self.ns.flags:
                start_it = True
            elif "load" in self.ns.flags:
                start_it = False

            if "queue" in self.ns.flags:
                queue_it = True

            # Load metafile into client
            load_cmd = self.job.proxy.load.verbose
            if queue_it:
                if not start_it:
                    self.ns.commands.append("d.priority.set=0")
            elif start_it:
                load_cmd = self.job.proxy.load.start_verbose

            self.job.LOG.debug("Templating values are:\n    %s" % "\n    ".join("%s=%s" % (key, repr(val))
                for key, val in sorted(self.ns.items())
            ))

            load_cmd(xmlrpc.NOHASH, self.ns.pathname, *tuple(self.ns.commands))
            time.sleep(.05) # let things settle

            # Announce new item
            if not self.job.config.quiet:
                msg = "%s: Loaded '%s' from '%s/'%s%s" % (
                    self.job.__class__.__name__,
                    fmt.to_utf8(self.job.proxy.d.name(self.ns.info_hash, fail_silently=True)),
                    os.path.dirname(self.ns.pathname).rstrip(os.sep),
                    " [queued]" if queue_it else "",
                    (" [startable]"  if queue_it else " [started]") if start_it else " [normal]",
                )
                self.job.proxy.log(xmlrpc.NOHASH, msg)

            # TODO: Evaluate fields and set client values
            # TODO: Add metadata to tied file if requested

            # TODO: Execute commands AFTER adding the item, with full templating
            # Example: Labeling - add items to a persistent view, i.e. "postcmd = view.set_visible={{label}}"
            #   could also be done automatically from the path, see above under "flags" (autolabel = True)
            #   and add traits to the flags, too, in that case

        except xmlrpc.ERRORS as exc:
            self.job.LOG.error("While loading #%s: %s" % (self.ns.info_hash, exc))


    def handle(self):
        """ Handle metafile.
        """
        if self.parse():
            self.load()


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
        self.job = kw["job"] # pylint: disable=W0201


    def handle_path(self, event):
        """ Handle a path-related event.
        """
        self.job.LOG.debug("Notification %r" % event)
        if event.dir:
            return

        if any(event.pathname.endswith(i) for i in self.METAFILE_EXT):
            MetafileHandler(self.job, event.pathname).handle()
        elif os.path.basename(event.pathname) == "watch.ini":
            self.job.LOG.info("NOT YET Reloading watch config for '%s'" % event.path)
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
        if self.job.LOG.isEnabledFor(logging.DEBUG):
            # On debug level, we subscribe to ALL events, so they're expected in that case ;)
            if self.job.config.trace_inotify:
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

        self.config.quiet = bool_param("quiet", False)
        self.config.queued = bool_param("queued", False)
        self.config.trace_inotify = bool_param("trace_inotify", False)

        self.config.path = set([os.path.abspath(os.path.expanduser(path.strip()).rstrip(os.sep))
            for path in self.config.path.split(os.pathsep)
        ])
        for path in self.config.path:
            if not os.path.isdir(path):
                raise error.UserError("Path '%s' is not a directory!" % path)

        # Assemble custom commands
        self.custom_cmds = {}
        for key, val in self.config.items():
            if key.startswith("cmd."):
                _, key = key.split('.', 1)
                if key in self.custom_cmds:
                    raise error.UserError("Duplicate custom command definition '%s'"
                        " (%r already registered, you also added %r)!" % (key, self.custom_cmds[key], val))
                self.custom_cmds[key] = formatting.preparse(val)
        self.LOG.debug("custom commands = %r" % self.custom_cmds)

        # Get client proxy
        self.proxy = xmlrpc.RTorrentProxy(configuration.scgi_url)
        self.proxy._set_mappings() # pylint: disable=W0212

        if self.config.active:
            self.setup()


    def setup(self):
        """ Set up inotify manager.

            See https://github.com/seb-m/pyinotify/.
        """
        if not pyinotify.WatchManager:
            raise error.UserError("You need to install 'pyinotify' to use %s (%s)!" % (
                self.__class__.__name__, pyinotify._import_error)) # pylint: disable=E1101, W0212

        self.manager = pyinotify.WatchManager()
        self.handler = TreeWatchHandler(job=self)
        self.notifier = pyinotify.AsyncNotifier(self.manager, self.handler)

        if self.LOG.isEnabledFor(logging.DEBUG):
            mask = pyinotify.ALL_EVENTS
        else:
            mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO # bogus pylint: disable=E1101

        # Add all configured base dirs
        for path in self.config.path:
            self.manager.add_watch(path.strip(), mask, rec=True, auto_add=True)


    def run(self):
        """ Regular maintenance and fallback task.
        """
        # TODO: Maybe do some stats logging here, once per hour or so
        # TODO: We can handle files that were not valid bencode here, from a Queue! And watch.ini reloading.

        # XXX: Add a check that the notifier is working, by creating / deleting a file
        # XXX: Also check for unhandled files

        # TODO: XXX: Especially on startup, we need to walk the directory tree
        #    and check for files not loaded (by checking hashes)!
        #    Or maybe rename them during loading?! Makes detection easy.

        # TODO: Move untied *.torrent.loaded in the tree to *.torrent.dead


class TreeWatchCommand(ScriptBaseWithConfig):
    ### Keep things wrapped to fit under this comment... ##############################
    """
        Use tree watcher directly from cmd line, call it like this:
            python -m pyrocore.torrent.watch <DIR>

        If the argument is a file, the templating namespace for that metafile is
        dumped (for testing and debugging purposes).
    """

    # log level for user-visible standard logging
    STD_LOG_LEVEL = logging.DEBUG

    # argument description for the usage information
    ARGS_HELP = "<directory>"

    OPTIONAL_CFG_FILES = ["torque.ini"]


    def mainloop(self):
        """ The main loop.
        """
        # Print usage if not enough args or bad options
        if len(self.args) < 1:
            self.parser.error("You have to provide the root directory of your watch tree, or a metafile path!")

        configuration.engine.load_config()

        pathname = os.path.abspath(self.args[0])
        if os.path.isdir(pathname):
            watch = TreeWatch(Bunch(path=pathname, job_name="watch", active=True, dry_run=True, load_mode=None))
            asyncore.loop(timeout=~0, use_poll=True)
        else:
            config = Bunch()
            config.update(dict((key.split('.', 2)[-1], val)
                for key, val in configuration.torque.items()
                if key.startswith("job.treewatch.")
            ))
            config.update(dict(path=os.path.dirname(os.path.dirname(pathname)), job_name="treewatch", active=False, dry_run=True))
            watch = TreeWatch(config)
            handler = MetafileHandler(watch, pathname)

            ok = handler.parse()
            self.LOG.debug("Metafile '%s' would've %sbeen loaded" % (pathname, "" if ok else "NOT "))

            if ok:
                handler.addinfo()
                post_process = str if self.options.verbose else logutil.shorten
                self.LOG.info("Templating values are:\n    %s" % "\n    ".join("%s=%s" % (key, post_process(repr(val)))
                    for key, val in sorted(handler.ns.items())
                ))


    @classmethod
    def main(cls): #pragma: no cover
        """ The entry point.
        """
        ScriptBase.setup()
        cls().run()


if __name__ == "__main__":
    TreeWatchCommand.main()
