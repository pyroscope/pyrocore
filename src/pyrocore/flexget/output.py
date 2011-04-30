""" Rtorrent Output Plugin.

    Copyright (c) 2011 The PyroScope Project <pyroscope.project@gmail.com>
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
from flexget import plugin, validator
#from flexget import feed as flexfeed
#from flexget.plugins import plugin_torrent

from pyrocore import error
from pyrocore import config as pyrocfg
from pyrocore.util import os, pymagic
#from pyrocore.torrent import engine


class Rtorrent(plugin.Plugin):
    """ Adds entries to a rTorrent client.
    """
    PRIO = 144
    
    def __init__(self, *args, **kw):
        """ Set plugin attribute defaults.
        """
        super(Rtorrent, self).__init__(*args, **kw)
        #self.LOG = pymagic.get_class_logger(self)
        self.proxy = None


    def validator(self):
        """ Our configuration model.
        """
        root = validator.factory()
        return root


    def _sanitize_config(self, config):
        """ Check config for correctness and make its content canonical.
        """
        if config in (True, False):
            # Enabled or disabled, with only defaults
            config = {"enabled": config}
        elif isinstance(config, basestring):
            # Only path to rtorrent config given
            config = {"rtorrent_rc": config}
        else:
            config = config.copy()
        
        config["rtorrent_rc"] = os.path.expanduser(config["config_dir"])

        return config


    def _open_proxy(self, config):
        """ Open proxy, if enabled and not yet open.
        """
        cfg = self._sanitize_config(config)
        if cfg and cfg["enabled"] and self.proxy is None:
            try:
                # Open the connection
                self.proxy = pyrocfg.engine.open()
                self.log.info(self.proxy) # where are we connected?
            except error.LoggableError, exc:
                raise plugin.PluginError(str(exc))

        return self.proxy


    def on_process_start(self, feed, config):
        """ Open the connection, if necessary.
        """
        ##LOG.warn("PROCSTART %r with %r" % (feed, config))
        self._open_proxy(config) # make things fail fast if they do


    def on_process_end(self, feed, config):
        """ Show final XMLRPC stats.
        """
        if self.proxy:
            self.log.info("XMLRPC stats: %s" % (self.proxy,))
            self.proxy = None


    def on_feed_start(self, feed, config):
        """ Feed starting.
        """
        self.config = self._sanitize_config(config)

                    
    def on_feed_exit(self, feed, config):
        """ Feed exiting.
        """
        self.config = None

    # Feed aborted, clean up
    on_feed_abort = on_feed_exit


    @plugin.priority(PRIO)
    def on_feed_output(self, feed, _):
        """ Load entries into rTorrent.
        """
        if not self.config["enabled"]:
            self.log.debugall("plugin disabled")
            return
        
        if self.proxy:
            try:
                pass
            except error.LoggableError, exc:
                raise plugin.PluginError(exc)

