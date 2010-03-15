""" PyroCore - Move seeding data.

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
from collections import defaultdict

#from pyrocore import config
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig
#from pyrocore.torrent import engine 


class RtorrentMove(ScriptBaseWithConfig):
    ### Keep things wrapped to fit under this comment... ##############################
    """ 
        Move data actively seeded in rTorrent.
    """

    # argument description for the usage information
    ARGS_HELP = "<source>... <target>"


    def add_options(self):
        """ Add program options.
        """
        super(RtorrentMove, self).add_options()

        # basic options
        self.add_bool_option("-n", "--dry-run",
            help="don't move data, just tell what would happen")


    def mainloop(self):
        """ The main loop.
        """
        # Print usage if not enough args
        if len(self.args) < 2:
            self.parser.print_help()
            self.parser.exit()

        # Preparation
        target = self.args[-1]
        source_paths = self.args[:-1]
        source_items = defaultdict(list)

        # Validation
        for path in source_paths:
            # TODO: Find item matching this source path
            source_items[path].append(None)

        # Actually move the data
        for path in source_paths:
            for item in source_items[path]:
                if not self.options.dry_run:
                    # Pause torrent?
                    item.pause()
        
                    # TODO: Move data and create symlink in its place
       
                    
                    # Resume torrent?
                    item.resume()


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    RtorrentMove().run()

