""" PyroCore - Metafile Creator.

    Copyright (c) 2009, 2010 The PyroScope Project <pyroscope.project@gmail.com>

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

import sys

from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig
from pyrocore.util import metafile, os


class MetafileCreator(ScriptBaseWithConfig):
    """ Create a bittorrent metafile.
    """

    # argument description for the usage information
    ARGS_HELP = "<dir-or-file> <tracker-url-or-alias>..."


    def add_options(self):
        """ Add program options.
        """
        super(MetafileCreator, self).add_options()

        self.add_bool_option("-p", "--private",
            help="disallow DHT and PEX")
        self.add_bool_option("--no-date",
            help="leave out creation date")
        self.add_value_option("-o", "--output-filename", "PATH",
            help="optional file name for the metafile")
        self.add_value_option("-r", "--root-name", "NAME",
            help="optional root name (default is basename of the data path)")
        self.add_value_option("-x", "--exclude", "PATTERN [-x ...]",
            action="append", default=[],
            help="exclude files matching a glob pattern from hashing")
        self.add_value_option("--comment", "TEXT",
            help="optional human-readable comment")
        self.add_value_option("-X", "--cross-seed", "LABEL",
            help="set explicit label for cross-seeding (changes info hash)")
        self.add_bool_option("-H", "--hashed", "--fast-resume",
            help="create second metafile containing libtorrent fast-resume information")
# TODO: Set "encoding" correctly
# TODO: Support multi-tracker extension ("announce-list" field)
# TODO: DHT "nodes" field?! [[str IP, int port], ...]
# TODO: Web-seeding http://www.getright.com/seedtorrent.html


    def mainloop(self):
        """ The main loop.
        """
        if not self.args:
            self.parser.print_help()
            self.parser.exit()
        elif len(self.args) < 2:
            self.parser.error("Expected a path and at least one announce URL, got: %s" % (' '.join(self.args),))

        def progress(totalhashed, totalsize):
            msg = " " * 30
            if totalhashed < totalsize:
                msg = "%5.1f%% complete" % (totalhashed * 100.0 / totalsize)
            sys.stdout.write(msg + " \r")
            sys.stdout.flush()

        if self.options.quiet:
            progress = None

        # Create and configure metafile factory
        datapath = self.args[0].rstrip(os.sep)
        metapath = datapath
        if self.options.output_filename:
            metapath = self.options.output_filename
            if os.path.isdir(metapath):
                metapath = os.path.join(metapath, os.path.basename(datapath))
        torrent = metafile.Metafile(metapath + ".torrent")
        torrent.ignore.extend(self.options.exclude)

        def callback(meta):
            "Callback to set label and resume data."
            if self.options.cross_seed:
                meta["info"]["x_cross_seed_label"] = self.options.cross_seed

            if self.options.hashed:
                try:
                    metafile.add_fast_resume(meta, datapath)
                except EnvironmentError, exc:
                    self.fatal("Error making fast-resume data (%s)" % (exc,))
                    raise

        # Create and write the metafile(s)
        torrent.create(datapath, self.args[1:], progress=progress, 
            root_name=self.options.root_name, private=self.options.private, no_date=self.options.no_date,
            comment=self.options.comment, created_by="PyroScope %s" % self.version, callback=callback
        )


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    MetafileCreator().run()

