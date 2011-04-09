""" PyroCore - Perform raw XMLRPC calls.

    Copyright (c) 2010 The PyroScope Project <pyroscope.project@gmail.com>

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
import logging
from pprint import pformat

from pyrocore import config
from pyrocore.util import xmlrpc2scgi
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig


class RtorrentXmlRpc(ScriptBaseWithConfig):
    ### Keep things wrapped to fit under this comment... ##############################
    """ 
        Perform raw rTorrent XMLRPC calls, like "rtxmlrpc get_throttle_up_rate ''".
        Start arguments with "+" or "-" to indicate they're numbers (type i4 or i8).
    """

    # log level for user-visible standard logging
    STD_LOG_LEVEL = logging.DEBUG

    # argument description for the usage information
    ARGS_HELP = "<method> <args>..."


    def add_options(self):
        """ Add program options.
        """
        super(RtorrentXmlRpc, self).add_options()

        # basic options
        self.add_bool_option("-r", "--repr", help="show Python pretty-printed response")
        self.add_bool_option("-x", "--xml", help="show XML response")


    def mainloop(self):
        """ The main loop.
        """
        # Print usage if not enough args or bad options
        if len(self.args) < 1:
            self.parser.error("No method given!")
        if self.options.repr and self.options.xml:
            self.parser.error("You cannot combine --repr and --xml!")

        # Preparation
        method = self.args[0]

        raw_args = self.args[1:]
        if '=' in method:
            if raw_args:
                self.parser.error("Please don't mix rTorrent and shell argument styles!")
            method, raw_args = method.split('=', 1)
            raw_args = raw_args.split(',')
        
        args = []
        for arg in raw_args:
            # TODO: use the xmlrpc-c type indicators instead / additionally
            if arg and arg[0] in "+-":
                try:
                    arg = int(arg, 10)
                except (ValueError, TypeError), exc:
                    self.LOG.warn("Not a valid number: %r (%s)" % (arg, exc))
            elif arg and arg[0] == '[':
                arg = arg.split(',')
            args.append(arg)

        # Make the call
        proxy = config.engine.open()
        try:
            result = getattr(proxy, method)(raw_xml=self.options.xml, *tuple(args))
        except xmlrpc2scgi.ERRORS, exc:
            self.LOG.error("While calling %s(%s): %s" % (method, ", ".join(repr(i) for i in args), exc))
        else:
            if not self.options.quiet:
                if self.options.repr or hasattr(result, "__iter__"):
                    # Pretty-print if requested, or it's a collection and not a scalar
                    result = pformat(result)
                print result

        # XMLRPC stats
        self.LOG.debug("XMLRPC stats: %s" % config.engine._rpc)


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    RtorrentXmlRpc().run()

