# -*- coding: utf-8 -*-
# pylint: disable=
""" Perform raw XMLRPC calls.

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
import os
import sys
import logging
import tempfile
import xmlrpclib
from pprint import pformat

from pyrocore import config, error
from pyrocore.util import fmt, xmlrpc
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig


class RtorrentXmlRpc(ScriptBaseWithConfig):
    ### Keep things wrapped to fit under this comment... ##############################
    """
        Perform raw rTorrent XMLRPC calls, like "rtxmlrpc throttle.global_up.max_rate".

        Start arguments with "+" or "-" to indicate they're numbers (type i4 or i8).
        Use "[1,2,..." for arrays.
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
        self.add_bool_option("-i", "--as-import",
            help="execute each argument as a private command using 'import'")

        # TODO: Tempita with "result" object in namespace
        #self.add_value_option("-o", "--output-format", "FORMAT",
        #    help="pass result to a template for formatting")


    def mainloop(self):
        """ The main loop.
        """
        # Print usage if not enough args or bad options
        if len(self.args) < 1:
            self.parser.error("No method given!")
        if self.options.repr and self.options.xml:
            self.parser.error("You cannot combine --repr and --xml!")

        # Check for "import" style call
        tmp_import = None
        try:
            if self.options.as_import:
                with tempfile.NamedTemporaryFile(suffix='.rc', prefix='rtxmlrpc-', delete=False) as handle:
                    handle.write('\n'.join(self.args + ['']))
                    tmp_import = handle.name

                method = 'import'
                args = (xmlrpc.NOHASH, tmp_import)

            else:
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
                        arg = arg[1:].split(',')
                        if all(i.isdigit() for i in arg):
                            arg = [int(i, 10) for i in arg]
                    elif arg and arg[0] == '@':
                        if arg == '@-':
                            arg = sys.stdin.read()
                        else:
                            with open(os.path.expanduser(arg[1:]), 'rb') as handle:
                                arg = handle.read()
                        arg = xmlrpclib.Binary(arg)
                    args.append(arg)

            # Open proxy
            if not config.scgi_url:
                config.engine.load_config()
            if not config.scgi_url:
                self.LOG.error("You need to configure a XMLRPC connection, read"
                    " https://pyrocore.readthedocs.io/en/latest/setup.html")
            proxy = xmlrpc.RTorrentProxy(config.scgi_url)
            proxy._set_mappings()

            # Make the call
            try:
                result = getattr(proxy, method)(raw_xml=self.options.xml, *tuple(args))
            except xmlrpc.ERRORS, exc:
                self.LOG.error("While calling %s(%s): %s" % (method, ", ".join(repr(i) for i in args), exc))
                self.return_code = error.EX_NOINPUT if "not find" in getattr(exc, "faultString", "") else error.EX_DATAERR
            else:
                if not self.options.quiet:
                    if self.options.repr:
                        # Pretty-print if requested, or it's a collection and not a scalar
                        result = pformat(result)
                    elif hasattr(result, "__iter__"):
                        result = '\n'.join(i if isinstance(i, basestring) else pformat(i) for i in result)
                    print fmt.to_console(result)

        finally:
            if tmp_import and os.path.exists(tmp_import):
                os.remove(tmp_import)

        # XMLRPC stats
        self.LOG.debug("XMLRPC stats: %s" % proxy)


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    RtorrentXmlRpc().run()


if __name__ == "__main__":
    run()
