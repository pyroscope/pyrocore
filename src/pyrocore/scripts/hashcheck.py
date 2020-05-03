# -*- coding: utf-8 -*-
# pylint: disable=
""" Metafile Checker.

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

from pyrobase import bencode
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig
from pyrocore.util import metafile, os


class MetafileChecker(ScriptBaseWithConfig):
    """ Check a bittorrent metafile.
    """

    # argument description for the usage information
    ARGS_HELP = "<metafile> [<data-dir-or-file>]"


    def add_options(self):  # pylint: disable=useless-super-delegation
        """ Add program options.
        """
        super(MetafileChecker, self).add_options()


    def mainloop(self):
        """ The main loop.
        """
        if not self.args:
            self.parser.print_help()
            self.parser.exit()
        elif len(self.args) < 1:
            self.parser.error("Expecting at least a metafile name")

        # Read metafile
        metapath = self.args[0]
        try:
            metainfo = bencode.bread(metapath)
        except (KeyError, bencode.BencodeError) as exc:
            self.fatal("Bad metafile %r (%s)" % (metapath, type(exc).__name__), exc)
            raise
        else:
            # Check metafile integrity
            try:
                metafile.check_meta(metainfo)
            except ValueError as exc:
                self.fatal("Metafile %r failed integrity check" % (metapath,), exc)
                raise
            else:
                if len(self.args) > 1:
                    datapath = self.args[1].rstrip(os.sep)
                else:
                    datapath = metainfo["info"]["name"]

                # Check the hashes
                torrent = metafile.Metafile(metapath)
                try:
                    ok = torrent.check(metainfo, datapath,
                        progress=None if self.options.quiet else metafile.console_progress())
                    if not ok:
                        self.fatal("Metafile %r has checksum errors" % (metapath,))
                        sys.exit(1)
                except OSError as exc:
                    self.fatal("Torrent data file missing", exc)
                    raise


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    MetafileChecker().run()


if __name__ == "__main__":
    run()
