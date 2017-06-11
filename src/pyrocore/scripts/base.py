# -*- coding: utf-8 -*-
# pylint: disable=
""" Command Line Script Support.

    Copyright (c) 2009, 2010 The PyroScope Project <pyroscope.project@gmail.com>
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
import glob
import time
import errno
import random
import textwrap
import logging.config
from optparse import OptionParser

import pkg_resources

from pyrocore import error, config
from pyrocore.util import os, fmt, pymagic, load_config


class ScriptBase(object):
    """ Base class for command line interfaces.
    """
    # logging configuration
    LOGGING_CFG = "~/.pyroscope/logging.%s.ini"

    # log level for user-visible standard logging
    STD_LOG_LEVEL = logging.INFO

    # argument description for the usage information
    ARGS_HELP = "<log-base>..."

    # additonal stuff appended after the command handler's docstring
    ADDITIONAL_HELP = []

    # Can be empty or None in derived classes
    COPYRIGHT = "Copyright (c) 2009 - 2017 Pyroscope Project"

    # Can be made explicit in derived classes (for external tools)
    VERSION = None


    @classmethod
    def setup(cls, cron_cfg="cron"):
        """ Set up the runtime environment.
        """
        random.seed()
        logging_cfg = cls.LOGGING_CFG
        if "%s" in logging_cfg:
            logging_cfg = logging_cfg % (cron_cfg if "--cron" in sys.argv[1:] else "scripts",)
        logging_cfg = os.path.expanduser(logging_cfg)

        if os.path.exists(logging_cfg):
            logging.HERE = os.path.dirname(logging_cfg)
            logging.config.fileConfig(logging_cfg)
        else:
            logging.basicConfig(level=logging.INFO)

        logging.getLogger().debug("Logging config read from '%s'" % logging_cfg)


    def _get_pkg_meta(self):
        """ Try to find package metadata.
        """
        pkg_info = "Version: 0.0.0\n"
        for info_ext, info_name in (('.egg-info', 'PKG-INFO'), ('.dist-info', 'METADATA')):
            try:
                # Development setup
                pkg_path = os.path.join(
                    __file__.split(__name__.replace('.', os.sep))[0], # containing path
                    __name__.split(".")[0] # package name
                )
                if os.path.exists(pkg_path + info_ext):
                    pkg_path += info_ext
                else:
                    globbed_paths = glob.glob(pkg_path + "-*-py%d.%d" % sys.version_info[:2] + info_ext)
                    if len(globbed_paths) == 1:
                        pkg_path = globbed_paths[0]
                    elif globbed_paths:
                        self.LOG.warn("Found %d release-specific candidate versions" % len(globbed_paths))
                        pkg_path = None
                    else:
                        globbed_paths = glob.glob(pkg_path + "-*" + info_ext)
                        if len(globbed_paths) == 1:
                            pkg_path = globbed_paths[0]
                        else:
                            self.LOG.warn("Found %d candidate versions" % len(globbed_paths))
                            pkg_path = None
                if pkg_path:
                    with open(os.path.join(pkg_path, info_name)) as handle:
                        pkg_info = handle.read()
                    break
                else:
                    self.LOG.warn("Software version cannot be determined!")
            except IOError:
                self.LOG.warn("Software version cannot be determined!")

        return pkg_info


    def __init__(self):
        """ Initialize CLI.
        """
        self.startup = time.time()
        self.LOG = pymagic.get_class_logger(self)

        # Get version number
        self.version = self.VERSION
        if not self.version:
            # Take version from package
            provider = pkg_resources.get_provider(__name__)
            pkg_meta = (provider.get_metadata("PKG-INFO")
                        or provider.get_metadata("METADATA")
                        or self._get_pkg_meta())
            pkg_dict = dict(line.split(": ", 1)
                for line in pkg_meta.splitlines()
                if ": " in line
            )
            self.version = pkg_dict.get("Version", "DEV")

        where = os.path.commonprefix([__file__, os.path.realpath(sys.argv[0]), sys.prefix])
        where = (where + os.sep).replace(os.path.expanduser('~' + os.sep), '~' + os.sep).rstrip(os.sep)
        self.version_info = '{}{}{} on Python {}'.format(
           self.version, ' from ' if where else '', where, sys.version.split()[0])

        self.args = None
        self.options = None
        self.return_code = 0
        self.parser = OptionParser(
            "%prog [options] " + self.ARGS_HELP + "\n\n"
            "%prog " + self.version_info + ('\n' + self.COPYRIGHT if self.COPYRIGHT else "") + "\n\n"
            + textwrap.dedent(self.__doc__.rstrip()).lstrip('\n')
            + '\n'.join(self.ADDITIONAL_HELP)
            + "\n\nFor more details, see the full documentation at"
            + "\n\n    https://pyrocore.readthedocs.io/",
            version="%prog " + self.version_info)


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
        self.add_bool_option("--debug",
            help="always show stack-traces for errors")
        self.add_bool_option("--cron",
            help="run in cron mode (with different logging configuration)")

        # Template method to add options of derived class
        self.add_options()

        self.handle_completion()
        self.options, self.args = self.parser.parse_args()

        # Override logging options in debug mode
        if self.options.debug:
            self.options.verbose = True
            self.options.quiet = False

        # Set logging levels
        if self.options.cron:
            self.STD_LOG_LEVEL = logging.DEBUG  # pylint: disable=invalid-name
        if self.options.verbose and self.options.quiet:
            self.parser.error("Don't know how to be quietly verbose!")
        elif self.options.quiet:
            logging.getLogger().setLevel(logging.WARNING)
        elif self.options.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        self.LOG.debug("Options: %s" % ", ".join("%s=%r" % i for i in sorted(vars(self.options).items())))


    def handle_completion(self):
        """ Handle shell completion stuff.
        """
        # We don't want these in the help, so handle them explicitely
        if len(sys.argv) > 1 and sys.argv[1].startswith("--help-completion-"):
            handler = getattr(self, sys.argv[1][2:].replace('-', '_'), None)
            if handler:
                print '\n'.join(sorted(handler()))
                self.STD_LOG_LEVEL = logging.DEBUG
                sys.exit(error.EX_OK)


    def help_completion_options(self):
        """ Return options of this command.
        """
        for opt in self.parser.option_list:
            for lopt in opt._long_opts:
                yield lopt


    def fatal(self, msg, exc=None):
        """ Exit on a fatal error.
        """
        if exc is not None:
            self.LOG.fatal("%s (%s)" % (msg, exc))
            if self.options.debug:
                return # let the caller re-raise it
        else:
            self.LOG.fatal(msg)
        sys.exit(error.EX_SOFTWARE)


    def run(self):
        """ The main program skeleton.
        """
        log_total = True

        try:
            try:
                # Preparation steps
                self.get_options()

                # Template method with the tool's main loop
                self.mainloop()
            except error.LoggableError, exc:
                if self.options.debug:
                    raise

                # Log errors caused by invalid user input
                try:
                    msg = str(exc)
                except UnicodeError:
                    msg = unicode(exc, "UTF-8")
                self.LOG.error(msg)
                sys.exit(error.EX_SOFTWARE)
            except KeyboardInterrupt, exc:
                if self.options.debug:
                    raise

                sys.stderr.write("\n\nAborted by CTRL-C!\n")
                sys.stderr.flush()
                sys.exit(error.EX_TEMPFAIL)
            except IOError, exc:
                # [Errno 32] Broken pipe?
                if exc.errno == errno.EPIPE:
                    sys.stderr.write("\n%s, exiting!\n" % exc)
                    sys.stderr.flush()

                    # Monkey patch to prevent an exception during logging shutdown
                    try:
                        handlers = logging._handlerList
                    except AttributeError:
                        pass
                    else:
                        for handler in handlers:
                            try:
                                handler.flush = lambda *_: None
                            except AttributeError:
                                pass # skip special handlers

                    log_total = False
                    sys.exit(error.EX_IOERR)
                else:
                    raise
        finally:
            # Shut down
            if log_total and self.options:  ## No time logging on --version and such
                running_time = time.time() - self.startup
                self.LOG.log(self.STD_LOG_LEVEL, "Total time: %.3f seconds." % running_time)
            logging.shutdown()

        # Special exit code?
        if self.return_code:
            sys.exit(self.return_code)


    def add_options(self):
        """ Add program options.
        """


    def mainloop(self):
        """ The main loop.
        """
        raise NotImplementedError()


class ScriptBaseWithConfig(ScriptBase):  # pylint: disable=abstract-method
    """ CLI tool with configuration support.
    """
    OPTIONAL_CFG_FILES = []


    def add_options(self):
        """ Add configuration options.
        """
        super(ScriptBaseWithConfig, self).add_options()

        self.add_value_option("--config-dir", "DIR",
            help="configuration directory [~/.pyroscope]")
        self.add_value_option("--config-file", "PATH",
            action="append", default=[],
            help="additional config file(s) to read")
        self.add_value_option("-D", "--define", "KEY=VAL [-D ...]",
            default=[], action="append", dest="defines",
            help="override configuration attributes")


    def get_options(self):
        """ Get program options.
        """
        super(ScriptBaseWithConfig, self).get_options()
        load_config.ConfigLoader(self.options.config_dir).load(self.OPTIONAL_CFG_FILES + self.options.config_file)
        if self.options.debug:
            config.debug = True

        for key_val in self.options.defines:
            try:
                key, val = key_val.split('=', 1)
            except ValueError, exc:
                raise error.UserError("Bad config override %r (%s)" % (key_val, exc))
            else:
                setattr(config, key, load_config.validate(key, val))


class PromptDecorator(object):
    """ Decorator for interactive commands.
    """

    # Return code for Q)uit choice
    QUIT_RC = error.EX_TEMPFAIL


    def __init__(self, script_obj):
        """ Initialize with containing tool object.
        """
        self.script = script_obj


    def add_options(self):
        """ Add program options, must be called in script's addOptions().
        """
        # These options need to be conflict-free to the containing
        # script, i.e. avoid short options if possible.
        self.script.add_bool_option("-i", "--interactive",
            help="interactive mode (prompt before changing things)")
        self.script.add_bool_option("--yes",
            help="positively answer all prompts (e.g. --delete --yes)")


    def ask_bool(self, question, default=True):
        """ Ask the user for Y)es / N)o / Q)uit.

            If "Q" ist entered, this method will exit with RC=3.
            Else, the user's choice is returned.

            Note that the options --non-interactive and --defaults
            also influence the outcome.
        """
        if self.script.options.yes:
            return True
        elif self.script.options.dry_run or not self.script.options.interactive:
            return default
        else:
            # Let the user decide
            choice = '*'
            while choice not in "YNAQ":
                choice = raw_input("%s? [%s)es, %s)o, a)ll yes, q)uit]: " % (
                    fmt.to_console(question), "yY"[int(default)], "Nn"[int(default)],
                ))
                choice = choice[:1].upper() or "NY"[int(default)]

            if choice == 'Q':
                self.quit()
            if choice == 'A':
                self.script.options.yes = True
                choice = 'Y'

            return choice == 'Y'


    def quit(self):
        """ Exit the program due to user's choices.
        """
        self.script.LOG.warn("Abort due to user choice!")
        sys.exit(self.QUIT_RC)
