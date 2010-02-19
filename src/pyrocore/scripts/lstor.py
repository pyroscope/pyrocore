""" PyroScope - Metafile Lister.

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
from pyroscope.util.bencode import BencodeError
from pyroscope.util.metafile import Metafile

LOG = logging.getLogger(__name__)


class MetafileLister(ScriptBase):
    """ List contents of a bittorrent metafile.
    """

    # argument description for the usage information
    ARGS_HELP = "<metafile>..."


    def add_options(self):
        """ Add program options.
        """


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
                lines = metafile.listing()
            except (KeyError, BencodeError), exc:
                LOG.warning("Bad metafile %r (%s: %s)" % (filename, type(exc).__name__, exc))
            else:
                print '\n'.join(lines)


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    MetafileLister().run()

