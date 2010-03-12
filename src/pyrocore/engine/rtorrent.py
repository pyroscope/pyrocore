# -*- coding: utf-8 -*-
# pylint: disable-msg=I0011
""" PyroCore - rTorrent Proxy.

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
import socket
import logging
from contextlib import closing

from pyrocore import config, error
from pyrocore.util import xmlrpc2scgi, load_config
from pyrocore.engine import base

LOG = logging.getLogger(__name__)


class RtorrentProxy(base.TorrentProxy):
    """ A single download item.
    """

    def __init__(self, engine, fields):
        """ Initialize download item.
        """
        super(RtorrentProxy, self).__init__()
        self._engine = engine
        self._fields = dict(fields)


    def start(self):
        """ (Re-)start downloading or seeding.
        """
        raise NotImplementedError()


    def stop(self):
        """ Stop and close download.
        """
        raise NotImplementedError()


class RtorrentEngine(base.TorrentEngine):
    """ The rTorrent backend proxy.
    """
    RTORRENT_RC_KEYS = ("scgi_local",)
    CONSTANT_FIELDS = set((
        "hash", "name", "is_private", "tracker_size", 
    ))
    PRE_FETCH_FIELDS = CONSTANT_FIELDS | set((
        "is_open", "complete",
        "ratio", "up_rate", "up_total", "down_rate", "down_total",
        "base_path", "tied_to_file", 
    ))
    FIELD_MAPPING = dict((v, k) for k, v in dict(
        is_complete = "complete",
        down = "down_rate",
        up = "up_rate",
        path = "base_path", 
        metafile = "tied_to_file", 
    ).items())


    def __init__(self):
        """ Initialize proxy.
        """
        super(RtorrentEngine, self).__init__()
        self._rpc = None
        self._session_dir = None
        self._download_dir = None
        self._items = None


    def _load_rtorrent_rc(self, namespace, rtorrent_rc=None):
        """ Load file given in "rtorrent_rc".
        """
        # Only load when needed (also prevents multiple loading)
        if not all(getattr(namespace, key, False) for key in self.RTORRENT_RC_KEYS):
            # Get and check config file name
            if not rtorrent_rc:
                rtorrent_rc = getattr(config, "rtorrent_rc", None)
            if not rtorrent_rc:
                raise error.UserError("No 'rtorrent_rc' path defined in configuration!")
            if not os.path.isfile(rtorrent_rc):
                raise error.UserError("Config file %r doesn't exist!" % (rtorrent_rc,))

            # Parse the file
            self.log.debug("Loading rtorrent config from %r" % (rtorrent_rc,))
            with closing(open(rtorrent_rc)) as handle:
                for line in handle.readlines():
                    # Skip comments and empty lines
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # Be lenient about errors, after all it's not our own config file
                    try:
                        key, val = line.split("=", 1)
                    except ValueError:
                        self.log.warning("Ignored invalid line %r in %r!" % (line, rtorrent_rc))
                        continue
                    key, val = key.strip(), val.strip()

                    # Copy values we're interested in
                    if key in self.RTORRENT_RC_KEYS:
                        print key, val
                    if key in self.RTORRENT_RC_KEYS and not getattr(namespace, key, None):
                        self.log.debug("Copied from rtorrent.rc: %s = %s" % (key, val))
                        setattr(namespace, key, val)

        # Validate fields
        for key in self.RTORRENT_RC_KEYS:
            setattr(namespace, key, load_config.validate(key, getattr(namespace, key)))
        if config.scgi_local.startswith("/"):
            config.scgi_local = "scgi://" + config.scgi_local


    def __repr__(self):
        """ Return a representation of internal state.
        """
        if self._rpc:
            # Connected state
            return "%s connected to %s [%s] via %r" % (
                self.__class__.__name__, self.engine_id, self.engine_software, config.scgi_local,
            )
        else:
            # Unconnected state
            self._load_rtorrent_rc(config)
            return "%s connectable via %r" % (
                self.__class__.__name__, config.scgi_local,
            )


    def open(self):
        """ Open connection.
        """
        # Only connect once
        if self._rpc is not None:
            return self._rpc

        # Get connection URL from rtorrent.rc
        self._load_rtorrent_rc(config)

        # Connect and get instance ID (also ensures we're connectable)
        self._rpc = xmlrpc2scgi.RTorrentXMLRPCClient(config.scgi_local)
        try:
            self.engine_id = self._rpc.get_name()
        except socket.error, exc:
            raise error.LoggableError("Can't connect to %s (%s)" % (config.scgi_local, exc))
        except Exception, exc:
            raise error.LoggableError("Can't connect to %s (%s)" % (config.scgi_local, exc))

        # Get other manifest values
        self.engine_software = "rTorrent %s/%s" % (
            self._rpc.system.client_version(), self._rpc.system.library_version(),
        )
        self.log.debug(repr(self))

        self._session_dir = self._rpc.get_session()
        self._download_dir = os.path.expanduser(self._rpc.get_directory())

        # Return connection
        return self._rpc


    def items(self):
        """ Get list of download items.
        """
        if self._items is None:
            items = []
            viewname = "main"
            args = [viewname] + ["d.%s%s=" % (
                    "" if field.startswith("is_") else "get_", field
                ) for field in self.PRE_FETCH_FIELDS
            ]
            for item in self.open().d.multicall(*tuple(args)):
                items.append(RtorrentProxy(self, zip(
                    [self.FIELD_MAPPING.get(i, i) for i in self.PRE_FETCH_FIELDS], item
                )))
                yield items[-1]
            self._items = items
        else:
            for item in self._items:
                yield item

