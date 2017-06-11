# -*- coding: utf-8 -*-
# pylint: disable=I0011
""" Configuration Loader.

    For details, see https://pyrocore.readthedocs.io/en/latest/setup.html

    Copyright (c) 2009, 2010, 2011 The PyroScope Project <pyroscope.project@gmail.com>
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
from __future__ import absolute_import

import re
import glob
import errno
import StringIO
import ConfigParser

from pyrocore import config, error
from pyrocore.util import os, pymagic


def validate(key, val):
    """ Validate a configuration value.
    """
    if val and val.startswith("~/"):
        return os.path.expanduser(val)
    if key == "output_header_frequency":
        return int(val, 10)
    if key.endswith("_ecma48"):
        return eval("'%s'" % val.replace("'", r"\'"))  # pylint: disable=eval-used

    return val


def walk_resources(package_or_requirement, resource_name, recurse=True, base=''):
    """ Yield paths of files in the given resource directory, all paths start with '/'.
    """
    base = base.rstrip('/') + '/'
    resource_base = (resource_name.rstrip('/') + '/' + base.strip('/')).rstrip('/')

    # Create default configuration files
    for filename in pymagic.resource_listdir(package_or_requirement, resource_base):
        # Skip hidden and other trashy names
        if filename.startswith('.') or any(filename.endswith(i) for i in (".pyc", ".pyo", "~")):
            continue

        # Handle subdirectories
        if pymagic.resource_isdir(package_or_requirement, resource_base + '/' + filename):
            if recurse:
                for i in walk_resources(package_or_requirement, resource_name, recurse, base=base + filename):
                    yield i
        else:
            yield base + filename


class ConfigLoader(object):
    """ Populates this module's dictionary with the user-defined configuration values.
    """
    CONFIG_INI = "config.ini"
    CONFIG_PY = "config.py"
    INTERPOLATION_ESCAPE = re.compile(r"(?<!%)%[^%(]")


    def __init__(self, config_dir=None):
        """ Create loader instance.
        """
        self.config_dir = config_dir or os.path.join(os.path.expanduser("~"), ".pyroscope")
        self.LOG = pymagic.get_class_logger(self)
        self._loaded = False


    def _update_config(self, namespace):  # pylint: disable=no-self-use
        """ Inject the items from the given dict into the configuration.
        """
        for key, val in namespace.items():
            setattr(config, key, val)


    def _interpolation_escape(self, namespace):
        """ Re-escape interpolation strings.
        """
        for key, val in namespace.items():
            if '%' in val:
                namespace[key] = self.INTERPOLATION_ESCAPE.sub(lambda match: '%' + match.group(0), val)


    def _validate_namespace(self, namespace):
        """ Validate the given namespace. This method is idempotent!
        """
        # Update config values (so other code can access them in the bootstrap phase)
        self._update_config(namespace)

        # Validate announce URLs
        for key, val in namespace["announce"].items():
            if isinstance(val, basestring):
                namespace["announce"][key] = val.split()

        # Re-escape output formats
        self._interpolation_escape(namespace["formats"])

        # Create objects from module specs
        for factory in ("engine",):
            if isinstance(namespace[factory], basestring):
                namespace[factory] = pymagic.import_name(namespace[factory])() if namespace[factory] else None

        # Do some standard type conversions
        for key in namespace:
            # Split lists
            if key.endswith("_list") and isinstance(namespace[key], basestring):
                namespace[key] = [i.strip() for i in namespace[key].replace(',', ' ').split()]

            # Resolve factory and callback handler lists
            elif any(key.endswith(i) for i in ("_factories", "_callbacks")) and isinstance(namespace[key], basestring):
                namespace[key] = [pymagic.import_name(i.strip()) for i in namespace[key].replace(',', ' ').split()]

        # Update config values again
        self._update_config(namespace)


    def _set_from_ini(self, namespace, ini_file):
        """ Copy values from loaded INI file to namespace.
        """
        # Isolate global values
        global_vars = dict((key, val)
            for key, val in namespace.items()
            if isinstance(val, basestring)
        )

        # Copy all sections
        for section in ini_file.sections():
            # Get values set so far
            if section == "GLOBAL":
                raw_vars = global_vars
            else:
                raw_vars = namespace.setdefault(section.lower(), {})

            # Override with values set in this INI file
            raw_vars.update(dict(ini_file.items(section, raw=True)))

            # Interpolate and validate all values
            if section == "FORMATS":
                self._interpolation_escape(raw_vars)
            raw_vars.update(dict(
                (key, validate(key, val))
                for key, val in ini_file.items(section, vars=raw_vars)
            ))

        # Update global values
        namespace.update(global_vars)


    def _set_defaults(self, namespace, optional_cfg_files):
        """ Set default values in the given dict.
        """
        # Add current configuration directory
        namespace["config_dir"] = self.config_dir

        # Load defaults
        for idx, cfg_file in enumerate([self.CONFIG_INI] + optional_cfg_files):
            if any(i in cfg_file for i in set('/' + os.sep)):
                continue # skip any non-plain filenames

            try:
                defaults = pymagic.resource_string("pyrocore", "data/config/" + cfg_file) #@UndefinedVariable
            except IOError as exc:
                if idx and exc.errno == errno.ENOENT:
                    continue
                raise

            ini_file = ConfigParser.SafeConfigParser()
            ini_file.optionxform = str # case-sensitive option names
            ini_file.readfp(StringIO.StringIO(defaults), "<defaults>")
            self._set_from_ini(namespace, ini_file)


    def _load_ini(self, namespace, config_file):
        """ Load INI style configuration.
        """
        self.LOG.debug("Loading %r..." % (config_file,))
        ini_file = ConfigParser.SafeConfigParser()
        ini_file.optionxform = str # case-sensitive option names
        if ini_file.read(config_file):
            self._set_from_ini(namespace, ini_file)
        else:
            self.LOG.warning("Configuration file %r not found,"
                             " use the command 'pyroadmin --create-config' to create it!" % (config_file,))


    def _load_py(self, namespace, config_file):
        """ Load scripted configuration.
        """
        if config_file and os.path.isfile(config_file):
            self.LOG.debug("Loading %r..." % (config_file,))
            exec(compile(open(config_file).read(), config_file, 'exec'),  # pylint: disable=exec-used
                 vars(config), namespace)
        else:
            self.LOG.warning("Configuration file %r not found!" % (config_file,))


    def load(self, optional_cfg_files=None):
        """ Actually load the configuation from either the default location or the given directory.
        """
        optional_cfg_files = optional_cfg_files or []

        # Guard against coding errors
        if self._loaded:
            raise RuntimeError("INTERNAL ERROR: Attempt to load configuration twice!")

        try:
            # Load configuration
            namespace = {}
            self._set_defaults(namespace, optional_cfg_files)

            self._load_ini(namespace, os.path.join(self.config_dir, self.CONFIG_INI))

            for cfg_file in optional_cfg_files:
                if not os.path.isabs(cfg_file):
                    cfg_file = os.path.join(self.config_dir, cfg_file)

                if os.path.exists(cfg_file):
                    self._load_ini(namespace, cfg_file)

            self._validate_namespace(namespace)
            self._load_py(namespace, namespace["config_script"])
            self._validate_namespace(namespace)

            for callback in namespace["config_validator_callbacks"]:
                callback()
        except ConfigParser.ParsingError as exc:
            raise error.UserError(exc)

        # Ready to go...
        self._loaded = True


    def create(self, remove_all_rc_files=False):
        """ Create default configuration files at either the default location or the given directory.
        """
        # Check and create configuration directory
        if os.path.exists(self.config_dir):
            self.LOG.debug("Configuration directory %r already exists!" % (self.config_dir,))
        else:
            os.mkdir(self.config_dir)

        if remove_all_rc_files:
            for subdir in ('.', 'rtorrent.d'):
                config_files = list(glob.glob(os.path.join(os.path.abspath(self.config_dir), subdir, '*.rc')))
                config_files += list(glob.glob(os.path.join(os.path.abspath(self.config_dir), subdir, '*.rc.default')))
                for config_file in config_files:
                    self.LOG.info("Removing %r!" % (config_file,))
                    os.remove(config_file)

        # Create default configuration files
        for filepath in sorted(walk_resources("pyrocore", "data/config")):
            # Load from package data
            text = pymagic.resource_string("pyrocore", "data/config" + filepath)

            # Create missing subdirs
            config_file = self.config_dir + filepath
            if not os.path.exists(os.path.dirname(config_file)):
                os.makedirs(os.path.dirname(config_file))

            # Write configuration files
            config_trail = [".default"]
            if os.path.exists(config_file):
                self.LOG.debug("Configuration file %r already exists!" % (config_file,))
            else:
                config_trail.append('')
            for i in config_trail:
                with open(config_file + i, "w") as handle:
                    handle.write(text)
                self.LOG.info("Configuration file %r written!" % (config_file + i,))
