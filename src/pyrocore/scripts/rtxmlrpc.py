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
from __future__ import absolute_import, print_function

import io
import os
import re
import sys
import glob
import logging
import tempfile
import textwrap
from pprint import pformat

try:
    import requests
except ImportError:
    requests = None

from six.moves import xmlrpc_client
import six

from pyrobase import bencode
from pyrobase.parts import Bunch

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
        To enter a XMLRPC REPL, pass no arguments at all.

        Start arguments with "+" or "-" to indicate they're numbers (type i4 or i8).
        Use "[1,2,..." for arrays. Use "@" to indicate binary data, which can be
        followed by a file path (e.g. "@/path/to/file"), a URL (https, http, ftp,
        and file are supported), or '-' to read from stdin.
    """

    # log level for user-visible standard logging
    STD_LOG_LEVEL = logging.DEBUG

    # argument description for the usage information
    ARGS_HELP = (
        "<method> <args>..."
        " |\n           -i <commands>... | -i @<filename> | -i @-"
        " |\n           --session <session-file>... | --session <directory>"
        " |\n           --session @<filename-list> | --session @-"
    )


    def add_options(self):
        """ Add program options.
        """
        super(RtorrentXmlRpc, self).add_options()

        # basic options
        self.add_bool_option("-r", "--repr", help="show Python pretty-printed response")
        self.add_bool_option("-x", "--xml", help="show XML response")
        self.add_bool_option("-i", "--as-import",
            help="execute each argument as a private command using 'import'")
        self.add_bool_option("--session", "--restore",
            help="restore session state from .rtorrent session file(s)")

        # TODO: Tempita with "result" object in namespace
        #self.add_value_option("-o", "--output-format", "FORMAT",
        #    help="pass result to a template for formatting")

        self.proxy = None


    def open(self):
        """Open connection and return proxy."""
        if not self.proxy:
            if not config.scgi_url:
                config.engine.load_config()
            if not config.scgi_url:
                self.LOG.error("You need to configure a XMLRPC connection, read"
                    " https://pyrocore.readthedocs.io/en/latest/setup.html")
            self.proxy = xmlrpc.RTorrentProxy(config.scgi_url)
            self.proxy._set_mappings()
        return self.proxy


    def cooked(self, raw_args):
        """Return interpreted / typed list of args."""
        args = []
        for arg in raw_args:
            # TODO: use the xmlrpc-c type indicators instead / additionally
            if arg and arg[0] in "+-":
                try:
                    arg = int(arg, 10)
                except (ValueError, TypeError) as exc:
                    self.LOG.warn("Not a valid number: %r (%s)" % (arg, exc))
            elif arg.startswith('[['):  # escaping, not a list
                arg = arg[1:]
            elif arg == '[]':
                arg = []
            elif arg.startswith('['):
                arg = arg[1:].split(',')
                if all(i.isdigit() for i in arg):
                    arg = [int(i, 10) for i in arg]
            elif arg.startswith('@'):
                arg = xmlrpc_client.Binary(read_blob(arg))
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
                result = fmt.xmlrpc_result_to_string(result, pretty=self.options.repr)
                output = getattr(sys.stdout, 'buffer', sys.stdout)
                output.write(fmt.to_console(result) + b"\n")

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


    def do_repl(self):
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


    def do_import(self):
        """Handle import files or streams passed with '-i'."""
        tmp_import = None
        try:
            if self.args[0].startswith('@') and self.args[0] != '@-':
                import_file = os.path.expanduser(self.args[0][1:])
                if not os.path.isfile(import_file):
                    self.parser.error("File not found (or not a file): {}".format(import_file))
                args = (xmlrpc.NOHASH, os.path.abspath(import_file))
            else:
                script_text = '\n'.join(self.args + [''])
                if script_text == '@-\n':
                    script_text = sys.stdin.read()

                with tempfile.NamedTemporaryFile(suffix='.rc', prefix='rtxmlrpc-', delete=False) as handle:
                    handle.write(script_text.encode('utf-8'))
                    tmp_import = handle.name
                args = (xmlrpc.NOHASH, tmp_import)

            self.execute(self.open(), 'import', args)
        finally:
            if tmp_import and os.path.exists(tmp_import):
                os.remove(tmp_import)


    def do_command(self):
        """Call a single command with arguments."""
        method = self.args[0]

        raw_args = self.args[1:]
        if '=' in method:
            if raw_args:
                self.parser.error("Please don't mix rTorrent and shell argument styles!")
            method, raw_args = method.split('=', 1)
            raw_args = raw_args.split(',')

        self.execute(self.open(), method, self.cooked(raw_args))


    def do_session(self):
        """Restore state from session files."""
        def filenames():
            'Helper'
            for arg in self.args:
                if os.path.isdir(arg):
                    for name in glob.glob(os.path.join(arg, '*.torrent.rtorrent')):
                        yield name
                elif arg == '@-':
                    for line in sys.stdin.read().splitlines():
                        if line.strip():
                            yield line.strip()
                elif arg.startswith('@'):
                    if not os.path.isfile(arg[1:]):
                        self.parser.error("File not found (or not a file): {}".format(arg[1:]))
                    with io.open(arg[1:], encoding='utf-8') as handle:
                        for line in handle:
                            if line.strip():
                                yield line.strip()
                else:
                    yield arg

        proxy = self.open()
        for filename in filenames():
            # Check filename and extract infohash
            self.LOG.debug("Reading '%s'...", filename)
            match = re.match(r'(?:.+?[-._])?([a-fA-F0-9]{40})(?:[-._].+?)?\.torrent\.rtorrent',
                             os.path.basename(filename))
            if not match:
                self.LOG.warn("Skipping badly named session file '%s'...", filename)
                continue
            infohash = match.group(1)

            # Read bencoded data
            try:
                with open(filename, 'rb') as handle:
                    raw_data = handle.read()
                data = Bunch(bencode.bdecode(raw_data))
            except EnvironmentError as exc:
                self.LOG.warn("Can't read '%s' (%s)" % (
                    filename, str(exc).replace(": '%s'" % filename, ""),
                ))
                continue

            ##print(infohash, '=', repr(data))
            if 'state_changed' not in data:
                self.LOG.warn("Skipping invalid session file '%s'...", filename)
                continue

            # Restore metadata
            was_active = proxy.d.is_active(infohash)
            proxy.d.ignore_commands.set(infohash, data.ignore_commands)
            proxy.d.priority.set(infohash, data.priority)

            if proxy.d.throttle_name(infohash) != data.throttle_name:
                proxy.d.pause(infohash)
                proxy.d.throttle_name.set(infohash, data.throttle_name)

            if proxy.d.directory(infohash) != data.directory:
                proxy.d.stop(infohash)
                proxy.d.directory_base.set(infohash, data.directory)

            for i in range(5):
                key = 'custom%d' % (i + 1)
                getattr(proxy.d, key).set(infohash, data[key])

            for key, val in data.custom.items():
                proxy.d.custom.set(infohash, key, val)

            for name in data.views:
                try:
                    proxy.view.set_visible(infohash, name)
                except xmlrpc_client.Fault as exc:
                    if 'Could not find view' not in str(exc):
                        raise

            if was_active and not proxy.d.is_active(infohash):
                (proxy.d.resume if proxy.d.is_open(infohash) else proxy.d.start)(infohash)
            proxy.d.save_full_session(infohash)

            """ TODO:
                NO public "set" command! 'timestamp.finished': 1503012786,
                NO public "set" command! 'timestamp.started': 1503012784,
                NO public "set" command! 'total_uploaded': 0,
            """


    def mainloop(self):
        """ The main loop.
        """
        self.check_for_connection()

        # Enter REPL if no args
        if len(self.args) < 1:
            return self.do_repl()

        # Check for bad options
        if self.options.repr and self.options.xml:
            self.parser.error("You cannot combine --repr and --xml!")
        if sum([self.options.as_import, self.options.session]) > 1:
            self.parser.error("You cannot combine -i and --session!")

        # Dispatch to handlers
        if self.options.as_import:
            self.do_import()
        elif self.options.session:
            self.do_session()
        else:
            self.do_command()

        # XMLRPC stats
        self.LOG.debug("XMLRPC stats: %s" % self.open())


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    RtorrentXmlRpc().run()


if __name__ == "__main__":
    run()
