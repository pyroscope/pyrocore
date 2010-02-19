""" PyroScope - Metafile Creator.

    Copyright (c) 2009 The PyroScope Project <pyroscope.project@gmail.com>

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
import sys
import logging

from pyroscope.scripts.base import ScriptBase
from pyroscope.util.metafile import Metafile

LOG = logging.getLogger(__name__)


class MetafileCreator(ScriptBase):
    """ Create a bittorrent metafile.
    """

    # argument description for the usage information
    ARGS_HELP = "<dir-or-file> <tracker-url>"


    def add_options(self):
        """ Add program options.
        """
        self.add_bool_option("-p", "--private",
            help="Disallow DHT and PEX")
        self.add_value_option("-o", "--output-filename", "PATH",
            help="Optional file name for the metafile")
        self.add_value_option("-r", "--root-name", "NAME",
            help="Optional root name (default is basename of the data path)")
        self.add_value_option("-x", "--exclude", "PATTERN",
            action="append", default=[],
            help="Exclude files matching a glob pattern from hashing")
        self.add_value_option("--comment", "TEXT",
            help="Optional human-readable comment")


    def mainloop(self):
        """ The main loop.
        """
        if not self.args:
            self.parser.print_help()
            self.parser.exit()
        elif len(self.args) != 2:
            self.parser.error("Expected exactly two arguments, got: %s" % (' '.join(self.args),))

        def progress(totalhashed, totalsize):
            msg = " " * 30
            if totalhashed < totalsize:
                msg = "%5.1f%% complete" % (totalhashed * 100.0 / totalsize)
            sys.stdout.write(msg + " \r")
            sys.stdout.flush()

        if self.options.quiet:
            progress = None

        datapath, tracker_url = self.args
        datapath = datapath.rstrip(os.sep)
        metafile = Metafile(self.options.output_filename or (datapath + ".torrent"))
        metafile.ignore.extend(self.options.exclude)
        metafile.create(datapath, tracker_url, progress=progress, 
            root_name=self.options.root_name, private=self.options.private,
            comment=self.options.comment, created_by="PyroScope %s" % self.version,
        )


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    MetafileCreator().run()

