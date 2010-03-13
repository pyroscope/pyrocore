""" PyroCore - rTorrent Control.

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

from pyrocore import config
from pyrocore.util import algo
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig
from pyrocore.torrent import engine, matching 


class RtorrentControl(ScriptBaseWithConfig):
    ### Keep things wrapped to fit under this comment... ##############################
    """ 
        Control and inspect rTorrent from the command line.
    
        Filter expressions take the form "<field>=<value>", and all expressions must
        be met (AND). If a field name is omitted, "name" is assumed.
        
        For numeric fields, a leading "+" means greater than, a leading "-" means 
        less than. For string fields, the value is a glob pattern (*, ?, [a-z]).
        Multiple values separated by a comma indicate several possible choices (OR).
        "!" in front of a filter value negates it.
        
        Examples:
          All 1:1 seeds             ratio=+1
          All active torrents       xfer=+0
          All seeding torrents      up=+0
          Slow torrents             down=+0 down=-5k
          Older than 2 weeks        age=+2w
          Big stuff                 size=+4g
          Music                     kind=flac,mp3
          1:1 seeds not on a NAS    ratio=+1 realpath=!/mnt/*
    """

    # argument description for the usage information
    ARGS_HELP = "<filter>..."

    # additonal stuff appended after the command handler's docstring
    ADDITIONAL_HELP = ["", "", "Fields are:",] + [
        "  %-21s %s" % (name, field.__doc__)
        for name, field in sorted(engine.FieldDefinition.FIELDS.items())
    ]


    def add_options(self):
        """ Add program options.
        """
        super(RtorrentControl, self).add_options()

        # basic options
        self.add_bool_option("-n", "--dry-run",
            help="don't commit changes, just tell what would happen")
        self.add_bool_option("-i", "--interactive",
            help="interactive mode (prompt before changing things)")
        self.add_bool_option("--yes",
            help="positively answer all prompts (e.g. --delete --yes)")
      
        # output control
        self.add_bool_option("-s", "--summary",
            help="print statistics")
        self.add_bool_option("-f", "--full",
            help="print full torrent details")
        self.add_value_option("-o", "--output-format", "FORMAT",
            default=r"  %(name)s\n    R:%(ratio)6.2f  U:%(up)9d  D:%(down)9d",
            help="specifiy display format")

        # torrent state change
        self.add_bool_option("-S", "--start",
            help="start torrent")
        self.add_bool_option("-C", "--close",
            help="stop torrent")
        self.add_bool_option("--delete",
            help="remove from client and archive metafile (implies -i)")
        self.add_bool_option("--purge", "--delete-data",
            help="remove from client and also delete all data (implies -i)")


    def mainloop(self):
        """ The main loop.
        """
        if not self.args:
            self.parser.print_help()
            self.parser.exit()

#        print repr(config.engine)
#        config.engine.open()
#        print repr(config.engine)

        # Do some escaping on output format
        self.options.output_format = (self.options.output_format
            .replace(r"\\", "\\")
            .replace(r"\n", "\n")
            .replace(r"\t", "\t")
            #.replace(r"\", "\")
        )                            

        # Parse filter conditions
        matcher = matching.CompoundFilterAll()
        for arg in self.args:
            matcher.append(engine.create_filter(arg))

        # Find matching torrents
        items = list(config.engine.items())
        match_count = 0
        for item in items:
            if matcher.match(item):
                match_count += 1

                # Print matching item
                print self.options.output_format % algo.AttributeMapping(item)

        self.LOG.info("Filtered %d out of %d torrents..." % (match_count, len(items),))
        ##print; print repr(items[0])
        
        # print summary
        if self.options.summary:
            # TODO
            pass


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    RtorrentControl().run()

