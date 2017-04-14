# -*- coding: utf-8 -*-
# pylint: disable=
""" Move seeding data.

    Copyright (c) 2010, 2011 The PyroScope Project <pyroscope.project@gmail.com>
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

import logging
from collections import defaultdict

from pyrocore import config
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig
from pyrocore.util import os, fmt, xmlrpc
#from pyrocore.torrent import engine


def pretty_path(path):
    """ Prettify path for logging.
    """
    path = fmt.to_utf8(path)
    home_dir = os.path.expanduser("~")
    if path.startswith(home_dir):
        path = "~" + path[len(home_dir):]
    return '"%s"' % (path,)


class RtorrentMove(ScriptBaseWithConfig):
    ### Keep things wrapped to fit under this comment... ##############################
    """
        Move data actively seeded in rTorrent.
    """

    # argument description for the usage information
    ARGS_HELP = "<source>... <target>"

    # fields needed to find the item
    PREFETCH_FIELDS = [
        "hash", "name", "size", "path", "is_complete",
    ]


    def add_options(self):
        """ Add program options.
        """
        super(RtorrentMove, self).add_options()

        # basic options
        self.add_bool_option("-n", "--dry-run",
            help="don't move data, just tell what would happen")
        self.add_bool_option("-F", "--force-incomplete",
            help="force a move of incomplete data")


    def resolve_slashed(self, path):
        """ Resolve symlinked directories if they end in a '/',
            remove trailing '/' otherwise.
        """
        if path.endswith(os.sep):
            path = path.rstrip(os.sep)
            if os.path.islink(path):
                real = os.path.realpath(path)
                self.LOG.debug('Resolved "%s/" to "%s"' % (path, real))
                path = real

        return path


    def guarded(self, call, *args):
        """ Catch exceptions thrown by filesystem calls, and don't really
            execute them in dry-run mode.
        """
        self.LOG.debug('%s(%s)' % (
            call.__name__, ', '.join([pretty_path(i) for i in args]),
        ))
        if not self.options.dry_run:
            try:
                call(*args)
            except (EnvironmentError, UnicodeError) as exc:
                self.fatal('%s(%s) failed [%s]' % (
                    call.__name__, ', '.join([pretty_path(i) for i in args]), exc,
                ))


    def mainloop(self):
        """ The main loop.
        """
        # Print usage if not enough args
        if len(self.args) < 2:
            self.parser.print_help()
            self.parser.exit()

        # TODO: Add mode to move tied metafiles, without losing the tie

        # Target handling
        target = self.args[-1]
        if "//" in target.rstrip('/'):
            # Create parts of target path
            existing, _ = target.split("//", 1)
            if not os.path.isdir(existing):
                self.fatal("Path before '//' MUST exists in %s" % (pretty_path(target),))

            # Possibly create the rest
            target = target.replace("//", "/")
            if not os.path.exists(target):
                self.guarded(os.makedirs, target)

        # Preparation
        # TODO: Handle cases where target is the original download path correctly!
        #       i.e.   rtmv foo/ foo   AND   rtmv foo/ .   (in the download dir)
        proxy = config.engine.open()
        download_path = os.path.realpath(os.path.expanduser(proxy.directory.default(xmlrpc.NOHASH).rstrip(os.sep)))
        target = self.resolve_slashed(target)
        source_paths = [self.resolve_slashed(i) for i in self.args[:-1]]
        source_realpaths = [os.path.realpath(i) for i in source_paths]
        source_items = defaultdict(list) # map of source path to item
        items = list(config.engine.items(prefetch=self.PREFETCH_FIELDS))

        # Validate source paths and find matching items
        for item in items:
            if not item.path:
                continue

            realpath = None
            try:
                realpath = os.path.realpath(item.path)
            except (EnvironmentError, UnicodeError) as exc:
                self.LOG.warning("Cannot realpath %r (%s)" % (item.path, exc))

            # Look if item matches a source path
            # TODO: Handle download items nested into each other!
            try:
                path_idx = source_realpaths.index(realpath or fmt.to_utf8(item.path))
            except ValueError:
                continue

            if realpath:
                self.LOG.debug('Item path %s resolved to %s' % (pretty_path(item.path), pretty_path(realpath)))
            self.LOG.debug('Found "%s" for %s' % (fmt.to_utf8(item.name), pretty_path(source_paths[path_idx])))
            source_items[source_paths[path_idx]].append(item)

        ##for path in source_paths: print path, "==>"; print "  " + "\n  ".join(i.path for i in source_items[path])

        if not os.path.isdir(target) and len(source_paths) > 1:
            self.fatal("Can't move multiple files to %s which is no directory!" % (pretty_path(target),))

        # Actually move the data
        moved_count = 0
        for path in source_paths:
            item = None # Make sure there's no accidental stale reference

            if not source_items[path]:
                self.LOG.warn("No download item found for %s, skipping!" % (pretty_path(path),))
                continue

            if len(source_items[path]) > 1:
                self.LOG.warn("Can't handle multi-item moving yet, skipping %s!" % (pretty_path(path),))
                continue

            if os.path.islink(path):
                self.LOG.warn("Won't move symlinks, skipping %s!" % (pretty_path(path),))
                continue

            for item in source_items[path]:
                if os.path.islink(item.path) and os.path.realpath(item.path) != os.readlink(item.path):
                    self.LOG.warn("Can't handle multi-hop symlinks yet, skipping %s!" % (pretty_path(path),))
                    continue

                if not item.is_complete:
                    if self.options.force_incomplete:
                        self.LOG.warn("Moving incomplete item '%s'!" % (item.name,))
                    else:
                        self.LOG.warn("Won't move incomplete item '%s'!" % (item.name,))
                        continue

                moved_count += 1
                dst = target
                if os.path.isdir(dst):
                    dst = os.path.join(dst, os.path.basename(path))
                self.LOG.info("Moving to %s..." % (pretty_path(dst),))

                # Pause torrent?
                # was_active = item.is_active and not self.options.dry_run
                # if was_active: item.pause()

                # TODO: move across devices
                # TODO: move using "d.directory.set" instead of symlinks
                if os.path.islink(item.path):
                    if os.path.abspath(dst) == os.path.abspath(item.path.rstrip(os.sep)):
                        # Moving back to original place
                        self.LOG.debug("Unlinking %s" % (pretty_path(item.path),))
                        self.guarded(os.remove, item.path)
                        self.guarded(os.rename, path, dst)
                    else:
                        # Moving to another place
                        self.LOG.debug("Re-linking %s" % (pretty_path(item.path),))
                        self.guarded(os.rename, path, dst)
                        self.guarded(os.remove, item.path)
                        self.guarded(os.symlink, os.path.abspath(dst), item.path)
                else:
                    # Moving download initially
                    self.LOG.debug("Symlinking %s" % (pretty_path(item.path),))
                    src1, src2 = os.path.join(download_path, os.path.basename(item.path)), fmt.to_unicode(os.path.realpath(path))
                    assert src1 == src2, 'Item path %r should match %r!' % (src1, src2)
                    self.guarded(os.rename, item.path, dst)
                    self.guarded(os.symlink, os.path.abspath(dst), item.path)

                # Resume torrent?
                # if was_active: sitem.resume()

        # Print stats
        self.LOG.debug("XMLRPC stats: %s" % proxy)
        self.LOG.log(logging.DEBUG if self.options.cron else logging.INFO, "Moved %d path%s (skipped %d)" % (
            moved_count, "" if moved_count == 1 else "s", len(source_paths) - moved_count
        ))


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    RtorrentMove().run()


if __name__ == "__main__":
    run()
