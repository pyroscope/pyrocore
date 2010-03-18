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
import re
import sys
import operator

from pyrocore import config
from pyrocore.util import fmt
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig
from pyrocore.torrent import engine 


class RtorrentControl(ScriptBaseWithConfig):
    ### Keep things wrapped to fit under this comment... ##############################
    """ 
        Control and inspect rTorrent from the command line.
    
        Filter expressions take the form "<field>=<value>", and all expressions must
        be met (AND). If a field name is omitted, "name" is assumed.
        
        For numeric fields, a leading "+" means greater than, a leading "-" means less 
        than. For string fields, the value is a glob pattern (*, ?, [a-z], [!a-z]).
        Multiple values separated by a comma indicate several possible choices (OR).
        "!" in front of a filter value negates it (NOT).
        
        Examples:
          All 1:1 seeds         ratio=+1
          All active torrents   xfer=+0
          All seeding torrents  up=+0
          Slow torrents         down=+0 down=-5k
          Older than 2 weeks    age=+2w
          Big stuff             size=+4g
          Music                 kind=flac,mp3
          1:1 seeds not on NAS  ratio=+1 realpath=!/mnt/*
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
# TODO: implement -i, --yes
#        self.add_bool_option("-i", "--interactive",
#            help="interactive mode (prompt before changing things)")
#        self.add_bool_option("--yes",
#            help="positively answer all prompts (e.g. --delete --yes)")
      
        # output control
        self.add_bool_option("-0", "--nul", "--print0",
            help="use a NUL character instead of a linebreak after items")
        #self.add_bool_option("-f", "--full",
        #    help="print full torrent details")
        self.add_value_option("-o", "--output-format", "FORMAT",
            help="specify display format (use '-o-' to disable item display)")
        self.add_value_option("-s", "--sort-fields", "FIELD[,...]",
            help="fields used for sorting")
        self.add_bool_option("-r", "--reverse-sort",
            help="reverse the sort order")
# TODO: implement -S
#        self.add_bool_option("-S", "--summary",
#            help="print statistics")

        # torrent state change
        self.add_bool_option("-S", "--start",
            help="start torrent")
        self.add_bool_option("-C", "--close", "--stop",
            help="stop torrent")
        self.add_bool_option("-H", "--hash-check",
            help="hash-check torrent")
# TODO: --pause, --resume?
# TODO: --throttle?
# TODO: use a custom field, and add a field for it ("tags")
#       & make the name of the custom field a config option 
#        self.add_bool_option("-T", "--tag", "[-]TAG",
#            help="set or remove a tag like 'manual'")
# TODO: implement --delete
#        self.add_bool_option("--delete",
#            help="remove from client and archive metafile (implies -i)")
# TODO: implement --purge
#        self.add_bool_option("--purge", "--delete-data",
#            help="remove from client and also delete all data (implies -i)")
# TODO: implement --move-data
#        self.add_value_option("--move-data", "DIR",
#            help="move data to given target directory (implies -i, can be combined with --delete)")


    def emit(self, item, defaults=None):
        """ Print an item to stdout.
        """
        item_text = fmt.to_console(self.options.output_format % engine.OutputMapping(item, defaults)) 
        if self.options.nul:
            sys.stdout.write(item_text + '\0')
            sys.stdout.flush()
        else: 
            print item_text 


    def validate_output_format(self, default_format):
        """ Prepare output format for later use.
        """
        output_format = self.options.output_format

        # Use default format if none is given
        if output_format is None:
            output_format = default_format

        # Expand plain field list to usable form
        if re.match(r"[,._0-9a-zA-Z]+", output_format):
            output_format = "%%(%s)s" % ")s\t%(".join(engine.validate_field_list(output_format))

        # Replace some escape sequences
        output_format = (output_format
            .replace(r"\\", "\\")
            .replace(r"\n", "\n")
            .replace(r"\t", "\t")
            .replace(r"\$", "\0") # the next 3 allow using $() instead of %()
            .replace("$(", "%(")
            .replace("\0", "$")
            .replace(r"\ ", " ") # to prevent stripping in config file
            #.replace(r"\", "\")
        )                            

        self.options.output_format = unicode(output_format)


    def validate_sort_fields(self):
        """ Take care of sorting.
        """
        sort_fields = self.options.sort_fields

        # Use default order if none is given
        if sort_fields is None:
            sort_fields = config.sort_fields

        # Split and validate field list
        sort_fields = engine.validate_field_list(sort_fields)

        self.options.sort_fields = sort_fields
        return operator.attrgetter(*tuple(self.options.sort_fields))


    def mainloop(self):
        """ The main loop.
        """
        # Print usage if no conditions are provided
        if not self.args:
            self.parser.error("No filter conditions given!")

        # Check options
        action_mode = sum([
            self.options.start, 
            self.options.close,
            self.options.hash_check,
        ])
        if action_mode > 1:
            self.parser.error("Options --start and --close are mutually exclusive")

#        print repr(config.engine)
#        config.engine.open()
#        print repr(config.engine)

        # Preparation steps
        self.validate_output_format(config.action_format if action_mode else config.output_format)
        sort_key = self.validate_sort_fields()
        matcher = engine.parse_filter_conditions(self.args)

        # Find matching torrents
        items = list(config.engine.items())
        matches = [item for item in items if matcher.match(item)]
        matches.sort(key=sort_key, reverse=self.options.reverse_sort)

        if action_mode:
            # Prepare action
            if self.options.start:
                action_name = "START"
                action = "start" 
            elif self.options.close:
                action_name = "CLOSE"
                action = "stop" 
            elif self.options.hash_check:
                action_name = "HASH"
                action = "hash_check" 
            self.LOG.info("About to %s %d out of %d torrents." % (action_name, len(matches), len(items),))

            # Perform chosen action on matches
            for item in matches:
                if self.options.output_format and self.options.output_format != "-":
                    self.emit(item, {"action": action_name}) 
                if not self.options.dry_run:
                    getattr(item, action)()
        else:
            # Display matches
            if self.options.output_format and self.options.output_format != "-":
                for item in matches:
                    # Print matching item
                    self.emit(item)

            self.LOG.info("Filtered %d out of %d torrents." % (len(matches), len(items),))

        ##print; print repr(items[0])
        
        # print summary
#        if self.options.summary:
#            # TODO
#            pass


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    RtorrentControl().run()

