""" PyroCore - Move seeding data.

    Copyright (c) 2010 The PyroScope Project <pyroscope.project@gmail.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
from collections import defaultdict

from pyrocore import config
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig
from pyrocore.util import os
#from pyrocore.torrent import engine 


def pretty_path(path):
    """ Prettify path from logging.
    """
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


    def mainloop(self):
        """ The main loop.
        """
        # Print usage if not enough args
        if len(self.args) < 2:
            self.parser.print_help()
            self.parser.exit()

        # Preparation
        # TODO: Handle cases where target is the original download path correctly!
        #       i.e.   rtmv foo/ foo   AND   rtmv foo/ .   (in the download dir)
        target = self.resolve_slashed(self.args[-1])
        source_paths = [self.resolve_slashed(i) for i in self.args[:-1]]
        source_realpaths = [os.path.realpath(i) for i in source_paths]
        source_items = defaultdict(list) # map of source path to item
        items = list(config.engine.items(prefetch=self.PREFETCH_FIELDS))

        # Validate source paths and find matching items
        for item in items:
            if not item.path:
                continue

            # Symlinked item?
            realpath = None
            if os.path.islink(item.path):
                try:
                    realpath = os.path.realpath(item.path)
                except (EnvironmentError, UnicodeError), exc:
                    self.LOG.warning("Cannot resolve symlink %r (%s)" % (item.path, exc))
            
            # Look if item matches a source path
            # TODO: Handle download items nested into each other!
            try:
                path_idx = source_realpaths.index(realpath or item.path)
            except ValueError:
                continue

            if realpath:
                self.LOG.debug('Item path "%s" resolved to "%s"' % (item.path, realpath))
            self.LOG.debug('Found "%s" for %r' % (item.name, source_paths[path_idx]))
            source_items[source_paths[path_idx]].append(item)

        ##for path in source_paths: print path, "==>"; print "  " + "\n  ".join(i.path for i in source_items[path])

        # Actually move the data
        def guarded(call, *args):
            "Helper for filesystem calls."
            self.LOG.debug('%s(%s)' % (
                call.__name__, ', '.join([pretty_path(i) for i in args]),
            ))
            if not self.options.dry_run:
                try:
                    call(*args)
                except (EnvironmentError, UnicodeError), exc:
                    self.fatal('%s(%s) failed [%s]' % (
                        call.__name__, ', '.join([pretty_path(i) for i in args]), exc,
                    ))

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

                self.LOG.info("Moving %s..." % (pretty_path(path),))
                moved_count += 1

                dst = target
                if os.path.isdir(dst):
                    dst = os.path.join(dst, os.path.basename(path))
                    self.LOG.info("    to %s" % (pretty_path(dst),))

                # Pause torrent?
                # was_active = item.is_active and not self.options.dry_run
                # if was_active: item.pause()

                # TODO: move across devices
                # TODO: move using "d.set_directory" instead of symlinks
                if os.path.islink(item.path):
                    if os.path.abspath(dst) == os.path.abspath(item.path.rstrip(os.sep)):
                        # Moving back to original place
                        self.LOG.info("Unlinking %s" % (pretty_path(item.path),))
                        guarded(os.remove, item.path)
                        guarded(os.rename, path, dst)
                    else:
                        # Moving to another place
                        self.LOG.debug("Re-linking %s" % (pretty_path(item.path),))
                        guarded(os.rename, path, dst)
                        guarded(os.remove, item.path)
                        guarded(os.symlink, os.path.abspath(dst), item.path)
                else:
                    # Moving download initially
                    self.LOG.info("Symlinking %s" % (pretty_path(item.path),))
                    assert os.path.abspath(item.path) == os.path.abspath(path), \
                        'Item path "%s" should match "%s"!' % (item.path, path)
                    guarded(os.rename, item.path, dst)
                    guarded(os.symlink, os.path.abspath(dst), item.path)

                # Resume torrent?
                # if was_active: sitem.resume()

        # Print stats
        self.LOG.debug("XMLRPC stats: %s" % config.engine._rpc)
        self.LOG.info("Moved %d path%s (skipped %d)" % (
            moved_count, "" if moved_count == 1 else "s", len(source_paths) - moved_count
        ))


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    RtorrentMove().run()

