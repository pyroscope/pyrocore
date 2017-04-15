# -*- coding: utf-8 -*-
# pylint: disable=
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

import re
import sys
import glob
import shutil
import pprint
import fnmatch
import urllib2
import xmlrpclib
from zipfile import ZipFile
from StringIO import StringIO
from contextlib import closing

from pyrobase import fmt
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig
from pyrocore import config, error
from pyrocore.util import os, load_config, metafile, matching


class AdminTool(ScriptBaseWithConfig):
    """ Support for administrative tasks.
    """

    # argument description for the usage information
    ARGS_HELP = ""

    # directories that should be created
    CONFIG_DIRS = ["log", "data", "run", "htdocs"]

    OPTIONAL_CFG_FILES = ["torque.ini"]

    RC_CONTINUATION_THRESHOLD = 55


    def add_options(self):
        """ Add program options.
        """
        super(AdminTool, self).add_options()

        self.add_bool_option("--create-config",
            help="create default configuration")
        self.add_bool_option("--remove-all-rc-files",
            help="write new versions of BOTH .rc and .rc.default files, and remove stale ones")
        self.add_bool_option("--dump-config",
            help="pretty-print configuration including all defaults")
        self.add_value_option("--create-import", "GLOB-PATTERN",
            action="append", default=[],
            help="create import file for a '.d' directory")
        self.add_bool_option("--dump-rc",
            help="pretty-print dynamic commands defined in 'rtorrent.rc'")
        self.add_value_option("-o", "--output", "KEY,KEY1.KEY2=DEFAULT,...",
            action="append", default=[],
            help="select fields to print, output is separated by TABs;"
                 " default values can be provided after the key")
        self.add_bool_option("--reveal",
            help="show config internals and full announce URL including keys")
        self.add_bool_option("--screenlet",
            help="create screenlet stub")


    def download_resource(self, download_url, target, guard):
        """ Helper to download and install external resources.
        """
        download_url = download_url.strip()
        if not os.path.isabs(target):
            target = os.path.join(config.config_dir, target)

        if os.path.exists(os.path.join(target, guard)):
            self.LOG.info("Already have '%s' in '%s'..." % (download_url, target))
            return

        if not os.path.isdir(target):
            os.makedirs(target)

        self.LOG.info("Downloading '%s' to '%s'..." % (download_url, target))
        with closing(urllib2.urlopen(download_url)) as url_handle:
            if download_url.endswith(".zip"):
                with closing(ZipFile(StringIO(url_handle.read()))) as zip_handle:  # pylint: disable=no-member
                    zip_handle.extractall(target)  # pylint: disable=no-member
            else:
                with open(os.path.join(target, guard), "wb") as file_handle:
                    shutil.copyfileobj(url_handle, file_handle)


    def mainloop(self):
        """ The main loop.
        """
        if self.options.create_config:
            # Create configuration
            config_loader = load_config.ConfigLoader(self.options.config_dir)
            config_loader.create(self.options.remove_all_rc_files)

            # Create directories
            for dirname in self.CONFIG_DIRS:
                dirpath = os.path.join(config_loader.config_dir, dirname)
                if not os.path.isdir(dirpath):
                    self.LOG.info("Creating %r..." % (dirpath,))
                    os.mkdir(dirpath)

            # Initialize webserver stuff
            if matching.truth(getattr(config, "torque", {}).get("httpd.active", "False"), "httpd.active"):
                self.download_resource(config.torque["httpd.download_url.smoothie"], "htdocs/js", "smoothie.js")

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

        elif self.options.create_import:
            conf_dirs = {}

            # Scan given directories
            for pattern in self.options.create_import:
                folder = os.path.expanduser(os.path.dirname(pattern))
                if not os.path.isdir(folder):
                    raise error.UserError("Parent of --create-import is not a directory: {}"
                                          .format(os.path.dirname(pattern)))

                # Read names of files to ignore
                ignore_file = os.path.join(folder, '.rcignore')
                rc_ignore = set(['.*', '*~'])
                if os.path.exists(ignore_file):
                    with open(ignore_file) as handle:
                        for line in handle:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                rc_ignore.add(line)

                folder = os.path.abspath(folder)
                files = glob.glob(os.path.join(folder, os.path.basename(pattern)))
                files = [x[len(folder+os.sep):] for x in files]
                files = [x for x in files if not any(fnmatch.fnmatch(x, i) for i in rc_ignore)]
                if not files:
                    self.LOG.warning("Pattern '{}' did not resolve to any files!".format(pattern))
                conf_dirs[folder] = files

            # Write ".rc" files
            for folder, files in conf_dirs.items():
                conf_rc = [
                    "# Include for '{}', generated {}".format(os.path.basename(folder), fmt.iso_datetime())
                ]
                folder = folder.replace(os.path.expanduser('~') + os.sep, '~' + os.sep)
                for name in sorted(files):
                    conf_rc.append('import = "{}{}{}"'.format(folder, os.sep, name))

                self.LOG.info("Creating %r..." % (folder + '/.import.rc',))
                with open(os.path.expanduser(folder + '/.import.rc'), 'wt') as handle:
                    handle.write('\n'.join(conf_rc + ['']))

        elif self.options.dump_rc:
            # list all dynamic commands
            proxy = config.engine.open()
            methods = proxy.system.listMethods()

            # XXX This is a heuristic and might break in newer rTorrent versions!
            builtins = set(methods[:methods.index('view.sort_new')+1])
            methods = set(methods)
            plain_re = re.compile(r'^[a-zA-Z0-9_.]+$')

            def is_method(name):
                'Helper'
                prefixes = ('d.', 'f.', 'p.', 't.', 'choke_group.', 'session.',
                    'system.', 'throttle.', 'trackers.', 'ui.', 'view.')

                if name.endswith('='):
                    name = name[:-1]
                return plain_re.match(name) and (
                    name in methods or
                    any(name.startswith(x) for x in prefixes))

            def rc_quoted(text, in_brace=False):
                'Helper'
                if isinstance(text, list):
                    wrap_fmt = '{%s}'
                    try:
                        method_name = text[0] + ""
                    except (TypeError, IndexError):
                        pass
                    else:
                        if is_method(method_name):
                            wrap_fmt = '(%s)' if in_brace else '((%s))'
                            if '.set' not in method_name and len(text) == 2 and text[1] == 0:
                                text = text[:1]
                    text = wrap_fmt % ', '.join([rc_quoted(x, in_brace=(wrap_fmt[0] == '{')) for x in text])
                    return text.replace('))))', ')) ))')
                elif isinstance(text, int):
                    return '{:d}'.format(text)
                elif plain_re.match(text) or is_method(text):
                    return text
                else:
                    return '"{}"'.format(text.replace('\\', '\\\\').replace('"', '\\"'))

            group = None
            for name in sorted(methods):
                try:
                    value = proxy.method.get('', name, fail_silently=True)
                    const = bool(proxy.method.const('', name, fail_silently=True))
                except xmlrpclib.Fault as exc:
                    if exc.faultCode == -503 and exc.faultString == 'Key not found.':
                        continue
                    raise
                else:
                    group, old_group = name.split('.', 1)[0], group
                    if group == 'event':
                        group = name
                    if group != old_group:
                        print('')

                    definition = None
                    objtype = type(value)
                    if objtype is list:
                        value = [rc_quoted(x) for x in value]
                        wrap_fmt = '((%s))' if value and is_method(value[0]) else '{%s}'
                        definition = wrap_fmt % ', '.join(value)
                    elif objtype is dict:
                        print('method.insert = {}, multi|rlookup|static'.format(name))
                        for key, val in sorted(value.items()):
                            val = rc_quoted(val)
                            if len(val) > self.RC_CONTINUATION_THRESHOLD:
                                val = '\\\n    ' + val
                            print('method.set_key = {}, {}, {}'.format(name, key, val))
                    elif objtype is str:
                        definition = rc_quoted(value)
                    elif objtype is int:
                        definition = '{:d}'.format(value)
                    else:
                        self.LOG.error("Cannot handle {!r} definition of method {}".format(objtype, name))
                        continue

                    if definition:
                        if name in builtins:
                            print('{}.set = {}'.format(name, definition))
                        else:
                            rctype = {str: 'string', int: 'value', long: 'value'}.get(objtype, 'simple')
                            if const:
                                rctype += '|const'
                                const = None
                            if len(definition) > self.RC_CONTINUATION_THRESHOLD:
                                definition = '\\\n    ' + definition
                            definition = (definition
                                .replace(" ;     ", " ;\\\n     ")
                                .replace(",    ", ",\\\n    ")
                            )
                            print('method.insert = {}, {}, {}'.format(name, rctype, definition))
                    if const:
                        print('method.const.enable = {}'.format(name))

        elif self.options.screenlet:
            # Create screenlet stub
            stub_dir = os.path.expanduser("~/.screenlets/PyroScope")
            if os.path.exists(stub_dir):
                self.fatal("Screenlet stub %r already exists" % stub_dir)

            stub_template = os.path.join(os.path.dirname(config.__file__), "data", "screenlet")
            shutil.copytree(stub_template, stub_dir)

            py_stub = os.path.join(stub_dir, "PyroScopeScreenlet.py")
            with open(py_stub, "w") as handle:
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
