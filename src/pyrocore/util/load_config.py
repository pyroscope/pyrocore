# -*- coding: utf-8 -*-
# pylint: disable-msg=I0011
""" PyroCore - Configuration Loader.

    For details, see http://code.google.com/p/pyroscope/wiki/UserConfiguration

    Copyright (c) 2009, 2010 The PyroScope Project <pyrocore.project@gmail.com>

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
import StringIO
import ConfigParser
import pkg_resources
from contextlib import closing

from pyrocore import config, error
from pyrocore.util import pymagic


def validate(key, val):
    """ Validate a configuration value.
    """
    if val.startswith("~/"):
        return os.path.expanduser(val)

    return val


class ConfigLoader(object):
    """ Populates this module's dictionary with the user-defined configuration values.
    """
    CONFIG_INI = "config.ini"
    CONFIG_PY = "config.py"


    def __init__(self, config_dir=None):
        """ Create loader instance.
        """
        self.config_dir = config_dir or os.path.join(os.path.expanduser("~"), ".pyroscope")
        self.LOG = pymagic.get_class_logger(self)
        self._loaded = False


    def _update_config(self, namespace):
        """ Inject the items from the given dict into the configuration.
        """
        for key, val in namespace.items():
            setattr(config, key, val)


    def _validate_namespace(self, namespace):
        """ Validate the given namespace. This method is idempotent!
        """
        # Update config values (so other code can access them in the bootstrap phase)
        self._update_config(namespace)

        # Validate announce URLs
        for key, val in namespace["announce"].items():
            if isinstance(val, basestring):
                namespace["announce"][key] = val.split()

        # Create objects from module specs
        for factory in ("engine",):
            if isinstance(namespace[factory], basestring):
                namespace[factory] = pymagic.import_name(namespace[factory])()

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
            raw_vars.update(dict(
                (key, validate(key, val))
                for key, val in ini_file.items(section, vars=raw_vars)
            ))

        # Update global values
        namespace.update(global_vars)


    def _set_defaults(self, namespace):
        """ Set default values in the given dict.
        """
        # Add current configuration directory
        namespace["config_dir"] = self.config_dir

        # Load defaults
        defaults = pkg_resources.resource_string("pyrocore", "data/config/config.ini") #@UndefinedVariable
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
            self.LOG.warning("Configuration file %r not found!" % (config_file,))


    def _load_py(self, namespace, config_file):
        """ Load scripted configuration.
        """
        if config_file and os.path.isfile(config_file):
            self.LOG.debug("Loading %r..." % (config_file,))
            execfile(config_file, vars(config), namespace)
        else:
            self.LOG.warning("Configuration file %r not found!" % (config_file,))
            

    def load(self):
        """ Actually load the configuation from either the default location or the given directory.
        """
        # Guard against coding errors
        if self._loaded:
            raise RuntimeError("INTERNAL ERROR: Attempt to load configuration twice!")

        try:
            # Load configuration
            namespace = {}
            self._set_defaults(namespace)
            self._load_ini(namespace, os.path.join(self.config_dir, self.CONFIG_INI))
            self._validate_namespace(namespace)
            self._load_py(namespace, namespace["config_script"])
            self._validate_namespace(namespace)
        except ConfigParser.ParsingError, exc:
            raise error.UserError(exc)

        # Ready to go...
        self._loaded = True


    def create(self):
        """ Create default configuration files either the default location or the given directory.
        """
        # Check and create configuration directory
        if os.path.exists(self.config_dir):
            self.LOG.warn("Configuration directory %r already exists!" % (self.config_dir,))
        else:
            os.mkdir(self.config_dir)

        # Create default configuration files
        for filename in pkg_resources.resource_listdir("pyrocore", "data/config"): #@UndefinedVariable
            # Skip hidden files
            if filename.startswith('.'):
                continue
            
            # Load default from package data
            text = pkg_resources.resource_string("pyrocore", "data/config/" + filename) #@UndefinedVariable

            # Check for existing configuration file
            config_file = os.path.join(self.config_dir, filename)
            if os.path.exists(config_file):
                self.LOG.warn("Configuration file %r already exists!" % (config_file,))
                config_file += ".default"

            # Write new configuration file
            with closing(open(config_file, "w")) as handle:
                handle.write(text)
            self.LOG.info("Configuration file %r written!" % (config_file,))
