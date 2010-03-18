""" PyroCore - Administration Tool.

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

import pprint

from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig
from pyrocore import config
from pyrocore.util import load_config, metafile


class AdminTool(ScriptBaseWithConfig):
    """ Support for administrative tasks.
    """

    # argument description for the usage information
    ARGS_HELP = ""


    def add_options(self):
        """ Add program options.
        """
        super(AdminTool, self).add_options()

        self.add_bool_option("--create-config",
            help="create default configuration")
        self.add_bool_option("--dump-config",
            help="pretty-print configuration including all defaults")
        self.add_bool_option("--reveal",
            help="show config internals and full announce URL including keys")


    def mainloop(self):
        """ The main loop.
        """
        if self.options.create_config:
            # Create configuration
            load_config.ConfigLoader(self.options.config_dir).create()
        elif self.options.dump_config:
            # Get public config attributes
            public = dict((key, val)
                for key, val in vars(config).items()
                if not key.startswith('_') and (self.options.reveal or not (
                    callable(val) or key in config._PREDEFINED
                ))
            )

            # Dump configuration
            pprinter = (pprint.PrettyPrinter if self.options.reveal else metafile.MaskingPrettyPrinter)() 
            pprinter.pprint(public)
        else:
            # Print usage
            self.parser.print_help()
            self.parser.exit()


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    AdminTool().run()

