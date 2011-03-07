""" PyroCore - Metafile Lister.

    Copyright (c) 2009, 2010, 2011 The PyroScope Project <pyroscope.project@gmail.com>

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
import pprint
import hashlib

from pyrocore.scripts.base import ScriptBase
from pyrocore.util import bencode, metafile


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
        self.add_bool_option("--raw",
            help="print the metafile's raw content in all detail")
        self.add_bool_option("-V", "--skip-validation",
            help="show broken metafiles with an invalid structure")
        self.add_value_option("-o", "--output", "KEY,KEY1.KEY2,...",
            action="append", default=[],
            help="select fields to print, output is separated by TABs;"
                 " note that __file__ is the path to the metafile"
                 " and __hash__ is the info hash")
        # TODO: implement this
        #self.add_value_option("-c", "--check-data", "PATH",
        #    help="check the hash against the data in the given path")

    def mainloop(self):
        """ The main loop.
        """
        if not self.args:
            self.parser.print_help()
            self.parser.exit()

        for idx, filename in enumerate(self.args):
            torrent = metafile.Metafile(filename)
            if idx and not self.options.output:
                print
                print "~" * 79
            try:
                # Read and check metafile
                try:
                    data = bencode.bread(filename)
                except EnvironmentError, exc:
                    self.fatal("Can't read '%s' (%s)" % (
                        filename, str(exc).replace(": '%s'" % filename, ""),
                    ))
                    raise
                try:
                    metafile.check_meta(data)
                except ValueError, exc:
                    if self.options.skip_validation:
                        self.LOG.warn(str(exc))
                    else:
                        raise
                listing = None

                if self.options.raw:
                    if not self.options.reveal:
                        # Shorten useless binary piece hashes
                        data["info"]["pieces"] = "<%d piece hashes>" % (
                            len(data["info"]["pieces"]) / len(hashlib.sha1().digest())
                        )

                    pprinter = (pprint.PrettyPrinter if self.options.reveal else metafile.MaskingPrettyPrinter)() 
                    listing = pprinter.pformat(data)
                elif self.options.output:
                    def splitter(fields):
                        "Yield single names for a list of comma-separated strings."
                        for flist in fields:
                            for field in flist.split(','):
                                yield field.strip()

                    data["__file__"] = filename
                    data["__hash__"] = metafile.info_hash(data)
                    values = []
                    for field in splitter(self.options.output):
                        try:
                            val = data
                            for key in field.split('.'):
                                val = val[key]
                        except KeyError, exc:
                            self.LOG.error("%s: Field %r not found (%s)" % (filename, field, exc))
                            break
                        else:
                            values.append(str(val))
                    else:
                        listing = '\t'.join(values)
                else:
                    listing = '\n'.join(torrent.listing(masked=not self.options.reveal))
            except (ValueError, KeyError, bencode.BencodeError), exc:
                self.LOG.warning("Bad metafile %r (%s: %s)" % (filename, type(exc).__name__, exc))
            else:
                if listing is not None:
                    print listing


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    MetafileLister().run()

