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
import xmlrpclib
from contextlib import closing

from pyrocore import config, error
from pyrocore.util import xmlrpc2scgi, load_config
from pyrocore.torrent import engine

# TODO: add stats counters to xmlrpc2scgi module (data transferred and calls made)


class RtorrentProxy(engine.TorrentProxy):
    """ A single download item.
    """

    def __init__(self, engine, fields):
        """ Initialize download item.
        """
        super(RtorrentProxy, self).__init__()
        self._engine = engine
        self._fields = dict(fields)


    def fetch(self, name):
        """ Get a field on demand.
        """
        try:
            return self._fields[name]
        except KeyError:
            if name == "done":
                self._fields[name] = float(self.fetch("completed_chunks")) / self.fetch("size_chunks") 
            else:
                getter_name = "get_" + RtorrentEngine.PYRO2RT_MAPPING.get(name, name)
                getter = getattr(self._engine._rpc.d, getter_name)
    
                try:
                    self._fields[name] = getter(self._fields["hash"])
                except xmlrpclib.Fault, exc:
                    raise error.EngineError("While accessing field %r: %s" % (name, exc))
    
            return self._fields[name]


    def announce_urls(self):
        """ Get a list of all announce URLs.
        """
        try:
            return [self._engine._rpc.t.get_url(self._fields["hash"], i) for i in range(self._fields["tracker_size"])]
        except xmlrpclib.Fault, exc:
            raise error.EngineError("While getting announce URLs for #%s: %s" % (self._fields["hash"], exc))


    def start(self):
        """ (Re-)start downloading or seeding.
        """
        try:
            self._engine._rpc.d.open(self._fields["hash"])
            self._engine._rpc.d.start(self._fields["hash"])
        except xmlrpclib.Fault, exc:
            raise error.EngineError("While starting torrent #%s: %s" % (self._fields["hash"], exc))


    def stop(self):
        """ Stop and close download.
        """
        try:
            self._engine._rpc.d.stop(self._fields["hash"])
            self._engine._rpc.d.close(self._fields["hash"])
        except xmlrpclib.Fault, exc:
            raise error.EngineError("While stopping torrent #%s: %s" % (self._fields["hash"], exc))


    def hash_check(self):
        """ Hash check a download.
        """
        try:
            self._engine._rpc.d.check_hash(self._fields["hash"])
        except xmlrpclib.Fault, exc:
            raise error.EngineError("While stopping torrent #%s: %s" % (self._fields["hash"], exc))


class RtorrentEngine(engine.TorrentEngine):
    """ The rTorrent backend proxy.
    """
    # keys we read from rTorrent's configuration
    RTORRENT_RC_KEYS = ("scgi_local",)

    # rTorrent names of fields that never change
    CONSTANT_FIELDS = set((
        "hash", "name", "is_private", "tracker_size", "size_bytes", 
    ))

    # rTorrent names of fields that never change
    PRE_FETCH_FIELDS = CONSTANT_FIELDS | set((
        "is_open", "complete",
        "ratio", "up_rate", "up_total", "down_rate", "down_total",
        "base_path", "tied_to_file", 
    ))

    # mapping of our names to rTorrent names (only those that differ)
    PYRO2RT_MAPPING = dict(
        is_complete = "complete",
        down = "down_rate",
        up = "up_rate",
        path = "base_path", 
        metafile = "tied_to_file", 
        size = "size_bytes",
        prio = "priority",
    )

    # inverse mapping of rTorrent names to ours
    RT2PYRO_MAPPING = dict((v, k) for k, v in PYRO2RT_MAPPING.items()) 


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
            self.LOG.debug("Loading rtorrent config from %r" % (rtorrent_rc,))
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
                        self.LOG.warning("Ignored invalid line %r in %r!" % (line, rtorrent_rc))
                        continue
                    key, val = key.strip(), val.strip()

                    # Copy values we're interested in
                    if key in self.RTORRENT_RC_KEYS and not getattr(namespace, key, None):
                        self.LOG.debug("rtorrent.rc: %s = %s" % (key, val))
                        setattr(namespace, key, val)

        # Validate fields
        for key in self.RTORRENT_RC_KEYS:
            setattr(namespace, key, load_config.validate(key, getattr(namespace, key)))
        # TODO: also support scgi://<scgi_port> connects
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

        # TODO: get system.time_usec and check for <i8> in raw response to ensure a working xmlrpc-c

        # Get other manifest values
        self.engine_software = "rTorrent %s/%s" % (
            self._rpc.system.client_version(), self._rpc.system.library_version(),
        )
        self.LOG.debug(repr(self))

        self._session_dir = self._rpc.get_session()
        self._download_dir = os.path.expanduser(self._rpc.get_directory())

        # Return connection
        return self._rpc


    def items(self):
        """ Get list of download items.
        """
        if self._items is None:
            # Prepare multi-call arguments
            viewname = "main"
            args = [viewname] + ["d.%s%s=" % (
                    "" if field.startswith("is_") else "get_", field
                ) for field in self.PRE_FETCH_FIELDS
            ]

            # Fetch items
            items = []
            try:
                ##self.LOG.debug("multicall %r" % (args,))
                raw_items = self.open().d.multicall(*tuple(args))
                ##import pprint; self.LOG.debug(pprint.pformat(raw_items))
                self.LOG.debug("Got %d items from %r" % (len(raw_items), self.engine_id))
                for item in raw_items:
                    items.append(RtorrentProxy(self, zip(
                        [self.RT2PYRO_MAPPING.get(i, i) for i in self.PRE_FETCH_FIELDS], item
                    )))
                    yield items[-1]
            except xmlrpclib.Fault, exc:
                raise error.EngineError("While getting download items from %r: %s" % (self, exc))

            # Just fetch once
            self._items = items
        else:
            # Yield prefetched results
            for item in self._items:
                yield item
