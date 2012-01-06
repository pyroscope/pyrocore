""" Administration Tool.

    Copyright (c) 2010 The PyroScope Project <pyroscope.project@gmail.com>
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
from __future__ import with_statement

import sys
import shutil
import pprint
from contextlib import closing

from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig
from pyrocore import config
from pyrocore.util import os, load_config, metafile


class AdminTool(ScriptBaseWithConfig):
    """ Support for administrative tasks.
    """

    # argument description for the usage information
    ARGS_HELP = ""

    # directories that should be created
    CONFIG_DIRS = ["log", "data"]
                
    def add_options(self):
        """ Add program options.
        """
        super(AdminTool, self).add_options()

        self.add_bool_option("--create-config",
            help="create default configuration")
        self.add_bool_option("--dump-config",
            help="pretty-print configuration including all defaults")
        self.add_value_option("-o", "--output", "KEY,KEY1.KEY2=DEFAULT,...",
            action="append", default=[],
            help="select fields to print, output is separated by TABs;"
                 " default values can be provided after the key")
        self.add_bool_option("--reveal",
            help="show config internals and full announce URL including keys")
        self.add_bool_option("--screenlet",
            help="create screenlet stub")


    def mainloop(self):
        """ The main loop.
        """
        if self.options.create_config:
            # Create configuration
            config_loader = load_config.ConfigLoader(self.options.config_dir)
            config_loader.create()

            # Create directories
            for dirname in self.CONFIG_DIRS:
                dirpath = os.path.join(config_loader.config_dir, dirname)
                if not os.path.isdir(dirpath):
                    self.LOG.info("Creating %r..." % (dirpath,))
                    os.mkdir(dirpath)

        elif self.options.dump_config or self.options.output:
            # Get public config attributes
            public = dict((key, val)
                for key, val in vars(config).items()
                if not key.startswith('_') and (self.options.reveal or not (
                    callable(val) or key in config._PREDEFINED
                ))
            )

            if self.options.dump_config:
                # Dump configuration
                pprinter = (pprint.PrettyPrinter if self.options.reveal else metafile.MaskingPrettyPrinter)() 
                pprinter.pprint(public)
            else:
                def splitter(fields):
                    "Yield single names for a list of comma-separated strings."
                    for flist in fields:
                        for field in flist.split(','):
                            yield field.strip()

                values = []
                for field in splitter(self.options.output):
                    default = None
                    if '=' in field:
                        field, default = field.split('=', 1)

                    try:
                        val = public
                        for key in field.split('.'):
                            if key in val:
                                val = val[key]
                            elif isinstance(val, list) and key.isdigit():
                                val = val[int(key, 10)]
                            else:
                                matches = [i for i in val.keys() if i.lower() == key.lower()]
                                if matches:
                                    val = val[matches[0]]
                                else:
                                    raise KeyError(key)
                    except (IndexError, KeyError), exc:
                        if default is None:
                            self.LOG.error("Field %r not found (%s)" % (field, exc))
                            break
                        values.append(default)
                    else:
                        values.append(str(val))
                else:
                    print '\t'.join(values)

        elif self.options.screenlet:
            # Create screenlet stub
            stub_dir = os.path.expanduser("~/.screenlets/PyroScope")
            if os.path.exists(stub_dir):
                self.fatal("Screenlet stub %r already exists" % stub_dir)

            stub_template = os.path.join(os.path.dirname(config.__file__), "data", "screenlet")
            shutil.copytree(stub_template, stub_dir)

            py_stub= os.path.join(stub_dir, "PyroScopeScreenlet.py")
            with closing(open(py_stub, "w")) as handle:
                handle.write('\n'.join([
                    "#! %s" % sys.executable,
                    "from pyrocore.screenlet.rtorrent import PyroScopeScreenlet, run",
                    "if __name__ == '__main__':",
                    "    run()",
                    "",
                ]))
            os.chmod(py_stub, 0755)
            
        else:
            # Print usage
            self.parser.print_help()
            self.parser.exit()


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    AdminTool().run()


if __name__ == "__main__":
    run()

