""" Rtorrent Connector Plugin.

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
import os
import logging

from flexget import plugin, validator
from flexget import feed as flexfeed
##from flexget.plugins import plugin_torrent

from pyrocore import error
from pyrocore import config as pyrocfg
from pyrocore.util import load_config, matching
from pyrocore.torrent import engine


# Global constants
LOG = logging.getLogger("rtorrent")


def _make_validator(schema):
    """ Make a configuration model.
    """
    root = validator.factory()
    params = root.accept("dict")
    for key, (kind, _) in schema.items():
        if ':' in kind:
            kind, val_kind = kind.split(':')
            params.accept(kind, key=key).accept_any_key(val_kind)
        else:
            params.accept(kind, key=key)

    return root


class RtorrentView(plugin.Plugin):
    """ Opens a rtorrent connection and does things to it.

        Example for dumping torrents matching a filter condition::
            feeds:
              pyrotest:
                rtorrent:
                  feed_query: 'loaded=-2d'
                quality: hdtv
                dump: yes

        Overriding the normal PyroScope configuration location::
            presets:
              global:
                rtorrent:
                  config_dir: ~/.pyroscope_flex
                  overrides:
                    rtorrent_rc: ~/bittorrent/rtorrent.rc
    """
    NAME = "rtorrent"

    # Only plugins below this prio can rely on the rtorrent connection
    PROXY_PRIO = 250
    
    PARAMS = {
        "enabled": ("boolean", True),           # enable the plugin?
        "config_dir": ("path", "~/.pyroscope"), # the PyroScope config dir
        "overrides": ("dict:text", {}),         # config override values
        "view": ("text", "main"),               # the view for feeding
        "feed_query": ("text", ""),             # a query condition (empty = off)
        #"feed_fields": ("list", []),
        #"feed_tied": ("", False,
    }

    def __init__(self, *args, **kw): # bogus super error pylint: disable=E1002
        """ Set plugin attribute defaults.
        """
        super(RtorrentView, self).__init__(*args, **kw)
        self.proxy = None
        self.global_config = None

    def validator(self):
        """ Our configuration model.
        """
        return _make_validator(self.PARAMS)

    def _sanitize_config(self, config):
        """ Check config for correctness and make its content canonical.
        """
        if config in (True, False):
            # Enabled or disabled, with only defaults
            config = {"enabled": config}
        elif isinstance(config, basestring):
            # Only path to pyroscope config given
            config = {"config_dir": config}
        else:
            config = config.copy()
        
        for key, (_, val) in self.PARAMS.items():
            config.setdefault(key, val)
            
        config["config_dir"] = os.path.expanduser(config["config_dir"])

        ##LOG.info("%08X %r" % (id(self), config))        
        return config

    def _open_proxy(self):
        """ Open proxy, if enabled and not yet open.
        """
        ##LOG.warn(repr(self.global_config))
        cfg = getattr(self, "config", self.global_config)
        
        if cfg and cfg["enabled"] and self.proxy is None:
            try:
                # Load config from disc
                load_config.ConfigLoader(cfg["config_dir"]).load()

                # Set overrides
                for key, val in cfg["overrides"].items():
                    setattr(pyrocfg, key, load_config.validate(key, val))

                # Open the connection
                self.proxy = pyrocfg.engine.open()
                LOG.info(pyrocfg.engine) # where are we connected?
            except error.LoggableError, exc:
                raise plugin.PluginError(str(exc))

        return self.proxy

    @plugin.priority(PROXY_PRIO)
    def on_process_start(self, feed, config):
        """ Open the connection, if necessary.
        """
        ##LOG.warn("PROCSTART %r with %r" % (feed, config))
        if self.global_config is None:
            rtorrent_preset = feed.manager.config.get("presets", {}).get("global", {}).get(self.NAME, {})
            ##LOG.warn("PRESET %r" % (rtorrent_preset,))
            self.global_config = self._sanitize_config(rtorrent_preset)
            self._open_proxy() # make things fail fast if they do

    def on_process_end(self, feed, config):
        """ Show final XMLRPC stats.
        """
        if self.proxy:
            LOG.info("XMLRPC stats: %s" % (self.proxy,))
            self.proxy = None

    def on_feed_start(self, feed, config):
        """ Feed starting.
        """
        self.config = self._sanitize_config(config)
        # XXX: ?Make sure global values aren't used on the local level?
            
    def on_feed_exit(self, feed, config):
        """ Feed exiting.
        """
        self.config = None

    # Feed aborted, clean up
    on_feed_abort = on_feed_exit

    def on_feed_input(self, feed, _):
        """ Produce entries from rtorrent items.
        """
        if not self.config["enabled"]:
            LOG.debugall("plugin disabled")
            return
        
        if self.proxy and self.config["feed_query"]:
            try:
                matcher = matching.ConditionParser(engine.FieldDefinition.lookup, "name").parse(self.config["feed_query"])
                view = pyrocfg.engine.view(self.config["view"], matcher)

                for item in view.items():
                    entry = flexfeed.Entry()
                    
                    entry["title"] = item.name
                    entry["url"] = "file://" + item.metafile
                    entry["uid"] = item.hash
                    entry["location"] = item.metafile

                    yield entry
            except error.LoggableError, exc:
                raise plugin.PluginError(exc)
