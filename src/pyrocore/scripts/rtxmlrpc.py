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
import textwrap
import xmlrpclib
from pprint import pformat

try:
    import requests
except ImportError:
    requests = None

from pyrocore import config, error
from pyrocore.util import fmt, xmlrpc
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig


def read_blob(arg):
    """Read a BLOB from given ``@arg``."""
    result = None
    if arg == '@-':
        result = sys.stdin.read()
    elif any(arg.startswith('@{}://'.format(x)) for x in {'http', 'https', 'ftp', 'file'}):
        if not requests:
            raise error.UserError("You must 'pip install requests' to support @URL arguments.")
        try:
            response = requests.get(arg[1:])
            response.raise_for_status()
            result = response.content
        except requests.RequestException as exc:
            raise error.UserError(str(exc))
    else:
        with open(os.path.expanduser(arg[1:]), 'rb') as handle:
            result = handle.read()

    return result


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


    def open(self):
        """Open connection and return proxy."""
        if not config.scgi_url:
            config.engine.load_config()
        if not config.scgi_url:
            self.LOG.error("You need to configure a XMLRPC connection, read"
                " https://pyrocore.readthedocs.io/en/latest/setup.html")
        proxy = xmlrpc.RTorrentProxy(config.scgi_url)
        proxy._set_mappings()
        return proxy


    def cooked(self, raw_args):
        """Return interpreted / typed list of args."""
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
                arg = xmlrpclib.Binary(read_blob(arg))
            args.append(arg)

        return args


    def execute(self, proxy, method, args):
        """Execute given XMLRPC call."""
        try:
            result = getattr(proxy, method)(raw_xml=self.options.xml, *tuple(args))
        except xmlrpc.ERRORS as exc:
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


    def repl_usage(self):
        """Print a short REPL usage summary."""
        print(textwrap.dedent("""
            rTorrent XMLRPC REPL Help Summary
            =================================

            ? / help            Show this help text.
            Ctrl-D              Exit the REPL and show call stats.
            stats               Show current call stats.
            cmd=arg1,arg2,..    Call a XMLRPC command.
        """.strip('\n')))


    def repl(self):
        """REPL for rTorrent XMLRPC commands."""
        from prompt_toolkit import prompt
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
        from prompt_toolkit.contrib.completers import WordCompleter

        self.options.quiet = False
        proxy = self.open()
        ps1 = proxy.session.name() + u'> '
        words = ['help', 'stats', 'exit']
        words += [x + '=' for x in proxy.system.listMethods()]
        history_file = os.path.join(config.config_dir, '.rtxmlrpc_history')

        while True:
            try:
                try:
                    cmd = prompt(ps1, completer=WordCompleter(words),
                                 auto_suggest=AutoSuggestFromHistory(),
                                 history=FileHistory(history_file))
                except KeyboardInterrupt:
                    cmd = ''
                if not cmd:
                    print("Enter '?' or 'help' for usage information, 'Ctrl-D' to exit.")

                if cmd in {'?', 'help'}:
                    self.repl_usage()
                    continue
                elif cmd in {'', 'stats'}:
                    print(repr(proxy).split(None, 1)[1])
                    continue
                elif cmd in {'exit'}:
                    raise EOFError()

                try:
                    method, raw_args = cmd.split('=', 1)
                except ValueError:
                    print("ERROR: '=' not found")
                    continue

                raw_args = raw_args.split(',')
                args = self.cooked(raw_args)
                self.execute(proxy, method, args)
            except EOFError:
                print('Bye from {!r}'.format(proxy))
                break


    def mainloop(self):
        """ The main loop.
        """
        # Enter REPL if no args
        if len(self.args) < 1:
            #self.parser.error("No method given!")
            return self.repl()

        # Check for bad options
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

                args = self.cooked(raw_args)

            # Make the call
            proxy = self.open()
            self.execute(proxy, method, args)
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
