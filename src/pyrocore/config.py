# -*- coding: utf-8 -*-
# pylint: disable-msg=I0011
""" PyroCore - Configuration.

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
# All imports go to the ConfigLoader methods to keep the namespace clean!


class _ConfigLoader(object):
    """ Populates this module's dictionary with the user-defined configuration values.
    """
    CONFIG_INI = "config.ini"
    CONFIG_PY = "config.py"


    def __init__(self):
        """ Create loader instance.
        """
        import logging
        
        self.config_dir = None
        self.log = logging.getLogger(self.__class__.__name__)
        self._loaded = False


    def _set_defaults(self, config, config_dir):
        """ Set default values.
        """
        import os

        # XXX Load defaults from "data/config/config.ini"?!
        config.update(dict(
            config_dir = config_dir,
            rtorrent_rc = os.path.join(os.path.expanduser("~"), ".rtorrent.rc")
        ))


    def create(self, config_dir=None):
        """ Create default configuration files either the default location or the given directory.
        """
        # TODO Implement this
        raise NotImplementedError()


    def load(self, config_dir=None):
        """ Actually load the configuation from either the default location or the given directory.
        """
        import os
        import logging
        # Guard against coding errors
        if self._loaded:
            raise RuntimeError("INTERNAL ERROR: Attempt to load configuration twice!")

        # Initialize stuff
        config = globals()
        config_dir = config_dir or os.path.join(os.path.expanduser("~"), ".pyroscope")
        self._set_defaults(config, config_dir)

        # TODO Load "config.ini"
        config_file = os.path.join(config_dir, self.CONFIG_INI)
        self.log.debug("Loading %r..." % (config_file,))

        # TODO Execute "config.py" in this module's namespace
        config_file = os.path.join(config_dir, self.CONFIG_PY)
        self.log.debug("Loading %r..." % (config_file,))
        local_ns = dict(
            LOG=logging.getLogger(__name__),
        )

        # Ready to go...
        self._loaded = True

