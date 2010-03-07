""" PyroCore - Command Line Script Support.

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
from __future__ import with_statement

import os
import sys
import time
import logging
import textwrap
import pkg_resources
from optparse import OptionParser
from contextlib import closing

LOG = logging.getLogger(__name__)


class ScriptBase(object):
    """ Base class for command line interfaces.
    """

    # argument description for the usage information
    ARGS_HELP = "<log-base>..."


    @classmethod
    def setup(cls):
        """ Set up the runtime environment.
        """
        logging.basicConfig(level=logging.INFO)


    def __init__(self):
        """ Initialize CLI.
        """
        self.startup = time.time()

        # Get version number
        provider = pkg_resources.get_provider(__name__)
        pkg_info = provider.get_metadata("PKG-INFO")
        if not pkg_info:
            # Development setup
            with closing(open(os.path.join(
                    __file__.split(__name__.replace('.', os.sep))[0],
                    __name__.split(".")[0] + ".egg-info", "PKG-INFO"))) as handle:
                pkg_info = handle.read()
        pkg_info = dict(line.split(": ", 1) 
            for line in pkg_info.splitlines() 
            if ": " in line
        )
        self.version = pkg_info.get("Version", "DEV")

        self.args = None
        self.options = None
        self.parser = OptionParser(
            "%prog [options] " + self.ARGS_HELP + "\n\n"
            "%prog " + self.version + ", Copyright (c) 2009, 2010 Pyroscope Project\n\n"
            + textwrap.dedent(self.__doc__.rstrip()).lstrip('\n'),
            version="%prog " + self.version)


    def add_bool_option(self, *args, **kwargs):
        """ Add a boolean option.

            @keyword help: Option description.
        """
        dest = [o for o in args if o.startswith("--")][0].replace("--", "").replace("-", "_")
        self.parser.add_option(dest=dest, action="store_true", default=False,
            help=kwargs['help'], *args)


    def add_value_option(self, *args, **kwargs):
        """ Add a value option.

            @keyword dest: Destination attribute, derived from long option name if not given.
            @keyword action: How to handle the option.
            @keyword help: Option description.
            @keyword default: If given, add this value to the help string.
        """
        kwargs['metavar'] = args[-1]
        if 'dest' not in kwargs:
            kwargs['dest'] = [o for o in args if o.startswith("--")][0].replace("--", "").replace("-", "_")
        if 'default' in kwargs and kwargs['default']:
            kwargs['help'] += " [%s]" % kwargs['default']
        self.parser.add_option(*args[:-1], **kwargs)


    def get_options(self):
        """ Get program options.
        """
        self.add_bool_option("-q", "--quiet",
            help="omit informational logging")
        self.add_bool_option("-v", "--verbose",
            help="increase informational logging")

        # Template method to add options of derived class
        self.add_options()

        self.options, self.args = self.parser.parse_args()

        if self.options.verbose and self.options.quiet:
            self.parser.error("Don't know how to be quietly verbose!")
        elif self.options.quiet:
            logging.getLogger().setLevel(logging.WARNING)
        elif self.options.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        LOG.debug("Options: %r" % self.options)


    def run(self):
        """ The main program skeleton.
        """
        # Preparation steps
        self.get_options()

        # Do the work
        try:
            # Template method with the tool's main loop
            self.mainloop()
        finally:
            # Shut down
            running_time = time.time() - self.startup
            LOG.info("Total time: %.3f seconds." % running_time)
            logging.shutdown()


    def add_options(self):
        """ Add program options.
        """


    def mainloop(self):
        """ The main loop.
        """
        raise NotImplementedError()



class ScriptBaseWithConfig(ScriptBase):
    """ CLI tool with configuration support.
    """

    def add_options(self):
        """ Add configuration options.
        """
        super(ScriptBaseWithConfig, self).add_options()

        self.add_value_option("--config-dir", "DIR",
            help="configuration directory [~/.pyroscope]")

