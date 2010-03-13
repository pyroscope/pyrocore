""" PyroCore - Metafile Lister.

    Copyright (c) 2009, 2010 The PyroScope Project <pyrocore.project@gmail.com>

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

from pyrocore.scripts.base import ScriptBase
from pyrocore.util.bencode import BencodeError
from pyrocore.util.metafile import Metafile


class MetafileLister(ScriptBase):
    """ List contents of a bittorrent metafile.
    """

    # argument description for the usage information
    ARGS_HELP = "<metafile>..."


    def add_options(self):
        """ Add program options.
        """
        self.add_bool_option("--reveal",
            help="show full announce URL including keys")
        # TODO implement this
        #self.add_value_option("-c", "--check-data", "PATH",
        #    help="check the hash against the data in the given path")


    def mainloop(self):
        """ The main loop.
        """
        if not self.args:
            self.parser.print_help()
            self.parser.exit()

        for idx, filename in enumerate(self.args):
            metafile = Metafile(filename)
            if idx:
                print
                print "~" * 79
            try:
                lines = metafile.listing(masked=not self.options.reveal)
            except (KeyError, BencodeError), exc:
                self.LOG.warning("Bad metafile %r (%s: %s)" % (filename, type(exc).__name__, exc))
            else:
                print '\n'.join(lines)


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    MetafileLister().run()

