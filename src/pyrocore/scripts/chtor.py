""" PyroCore - Metafile Editor.

    Copyright (c) 2010 The PyroScope Project <pyrocore.project@gmail.com>

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

import os
import urlparse

from pyrocore.scripts.base import ScriptBase
from pyrocore.util import bencode


class MetafileChanger(ScriptBase):
    """ Change attributes of a bittorrent metafile.
    """

    # argument description for the usage information
    ARGS_HELP = "<metafile>..."


    def add_options(self):
        """ Add program options.
        """
        self.add_bool_option("-n", "--dry-run",
            help="don't write changes to disk, just tell what would happen")
        ##self.add_value_option("-T", "--tracker", "DOMAIN",
        ##    help="filter given torrents for a tracker domain")
        self.add_value_option("-a", "--reannounce", "URL",
            help="set a new announce URL")


    def mainloop(self):
        """ The main loop.
        """
        if not self.args:
            self.parser.print_help()
            self.parser.exit()

        # set filter criteria for metafiles
        filter_url_prefix = None
        if self.options.reannounce:
            # <scheme>://<netloc>/<path>?<query>
            filter_url_prefix = urlparse.urlsplit(self.options.reannounce, allow_fragments=False)
            filter_url_prefix = urlparse.urlunsplit((
                filter_url_prefix.scheme, filter_url_prefix.netloc, '/', '', ''
            ))
            self.LOG.info("Filtering for metafiles with announce URL prefix %r..." % filter_url_prefix)

        # go through given files
        bad = 0
        changed = 0
        for filename in self.args:
            try:
                # read and remember current content
                metainfo = bencode.bread(filename)
                old_metainfo = bencode.bencode(metainfo)
            except (KeyError, bencode.BencodeError), exc:
                self.LOG.warning("Bad metafile %r (%s: %s)" % (filename, type(exc).__name__, exc))
                bad += 1
            else:
                # skip any metafile that don't meet the pre-conditions
                if filter_url_prefix and not metainfo['announce'].startswith(filter_url_prefix):
                    continue

                # change announce URL?
                if self.options.reannounce:
                    # XXX missing multi-tracker support
                    metainfo['announce'] = self.options.reannounce

                # Write new metafile, if changed
                new_metainfo = bencode.bencode(metainfo)
                if new_metainfo != old_metainfo:
                    self.LOG.info("Changing %r..." % filename)
                    changed += 1

                    if not self.options.dry_run:
                        # Write to temporary file
                        tempname = os.path.join(
                            os.path.dirname(filename),
                            '.' + os.path.basename(filename),
                        )
                        self.LOG.debug("Wriitng %r..." % tempname)
                        bencode.bwrite(tempname, metainfo)

                        # Replace existing file
                        if os.name != "posix":
                            # cannot rename to existing target on WIN32
                            os.remove(filename)
                        os.rename(tempname, filename)

        # print summary
        if changed:
            self.LOG.info("%s %d metafile(s)." % (
                "Would've changed" if self.options.dry_run else "Changed", changed
            ))
        if bad:
            self.LOG.warn("Skipped %d bad metafile(s)!" % (bad))


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    MetafileChanger().run()

