# -*- coding: utf-8 -*-
# pylint: disable-msg=I0011
""" PyroCore - rTorrent Proxy.

    Copyright (c) 2009, 2010 The PyroScope Project <pyroscope.project@gmail.com>

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


    def _make_it_so(self, command, calls, *args):
        """ Perform some error-checked XMLRPC calls.
        """
        args = (self._fields["hash"],) + args
        try:
            for call in calls:
                self._engine.LOG.debug("%s%s torrent #%s (%s)" % (
                    command[0].upper(), command[1:], self._fields["hash"], call))
                getattr(self._engine._rpc.d, call)(*args)
        except xmlrpclib.Fault, exc:
            raise error.EngineError("While %s torrent #%s: %s" % (command, self._fields["hash"], exc))


    def fetch(self, name, engine_name=None):
        """ Get a field on demand.
        """
        try:
            return self._fields[name]
        except KeyError:
            if name == "done":
                val = float(self.fetch("completed_chunks")) / self.fetch("size_chunks")
            elif name.startswith("custom_"):
                try:
                    val = self._engine._rpc.d.get_custom(self._fields["hash"], name.split('_', 1)[1])
                except xmlrpclib.Fault, exc:
                    raise error.EngineError("While accessing field %r: %s" % (name, exc))
            else:
                getter_name = "get_" + (engine_name if engine_name else RtorrentEngine.PYRO2RT_MAPPING.get(name, name))
                getter = getattr(self._engine._rpc.d, getter_name)
    
                try:
                    val = getter(self._fields["hash"])
                except xmlrpclib.Fault, exc:
                    raise error.EngineError("While accessing field %r: %s" % (name, exc))

            # TODO: Currently, NOT caching makes no sense; in a demon, it does!
            #if isinstance(FieldDefinition.FIELDS.get(name), engine.ConstantField):
            self._fields[name] = val

            return val


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
        self._make_it_so("starting", ["open", "start"])


    def stop(self):
        """ Stop and close download.
        """
        self._make_it_so("stopping", ["stop", "close"])


    def ignore(self, flag):
        """ Set ignore status.
        """
        self._make_it_so("setting ignore status for", ["set_ignore_commands"], int(flag))


    def tag(self, tags):
        """ Add or remove tags.
        """
        # Get tag list and add/remove given tags
        tags = tags.lower()
        previous = self.tagged
        tagset = previous.copy()
        for tag in tags.split():
            if tag.startswith('-'):
                tagset.discard(tag[1:])
            elif tag.startswith('+'):
                tagset.add(tag[1:])
            else:
                tagset.add(tag)

        # Write back new tagset, if changed
        tagset.discard('')
        if tagset != previous:
            tagset = ' '.join(sorted(tagset))
            self._make_it_so("setting tags %r on" % (tagset,), ["set_custom"], "tags", tagset)
            self._fields["custom_tags"] = tagset


    def set_throttle(self, name):
        """ Assign to throttle group.
        """
        if name.lower() == "null":
            name = "NULL"
        if name.lower() == "none":
            name = ""

        if (name or "NONE") not in config.throttle_names:
            raise error.UserError("Unknown throttle name %r" % (name or "NONE",))

        if (name or "NONE") == self.throttle:
            self._engine.LOG.debug("Keeping throttle %r on torrent #%s" % (self.throttle, self._fields["hash"]))
            return

        active = self.is_active
        if active:
            self._engine.LOG.debug("Torrent #%s stopped for throttling" % (self._fields["hash"],))
            self.stop()
        self._make_it_so("setting throttle %r on" % (name,), ["set_throttle_name"], name)
        if active:
            self._engine.LOG.debug("Torrent #%s restarted after throttling" % (self._fields["hash"],))
            self.start()


    def hash_check(self):
        """ Hash check a download.
        """
        self._make_it_so("hash-checking", ["check_hash"])


    def delete(self):
        """ Remove torrent from client.
        """
        self.stop()
        self._make_it_so("removing metafile of", ["delete_tied"])
        self._make_it_so("erasing", ["erase"])


    def flush(self):
        """ Write volatile data to disk.
        """
        self._make_it_so("saving session data of", ["save_session"])

    # TODO: purge is probably: get base_path, self.delete(), rm -rf base_path


class RtorrentEngine(engine.TorrentEngine):
    """ The rTorrent backend proxy.
    """
    # throttling config keys
    RTORRENT_RC_THROTTLE_KEYS = ("throttle_up", "throttle_down", "throttle_ip", )

    # keys we read from rTorrent's configuration
    RTORRENT_RC_KEYS = ("scgi_local", "scgi_port", ) + RTORRENT_RC_THROTTLE_KEYS

    # rTorrent names of fields that never change
    CONSTANT_FIELDS = set((
        "hash", "name", "is_private", "tracker_size", "size_bytes", 
    ))

    # rTorrent names of fields that get fetched in multi-call
    PRE_FETCH_FIELDS = CONSTANT_FIELDS | set((
        "is_open", "is_active", "complete",
        "ratio", "up_rate", "up_total", "down_rate", "down_total",
        "base_path", "tied_to_file", 
    ))

    # mapping of our names to rTorrent names (only those that differ)
    PYRO2RT_MAPPING = dict(
        is_complete = "complete",
        is_ignored = "ignore_commands",
        down = "down_rate",
        up = "up_rate",
        path = "base_path", 
        metafile = "tied_to_file", 
        size = "size_bytes",
        prio = "priority",
        throttle = "throttle_name",
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
                    if key in self.RTORRENT_RC_THROTTLE_KEYS:
                        val = val.split(',')[0].strip()
                        self.LOG.debug("rtorrent.rc: added throttle %r" % (val,))
                        namespace.throttle_names.add(val)
                    elif key in self.RTORRENT_RC_KEYS and not getattr(namespace, key, None):
                        self.LOG.debug("rtorrent.rc: %s = %s" % (key, val))
                        setattr(namespace, key, val)

        # Validate fields
        for key in self.RTORRENT_RC_KEYS:
            setattr(namespace, key, load_config.validate(key, getattr(namespace, key, None)))
        if config.scgi_local and config.scgi_local.startswith("/"):
            config.scgi_local = "scgi://" + config.scgi_local
        if config.scgi_port and not config.scgi_port.startswith("scgi://"):
            config.scgi_port = "scgi://" + config.scgi_port

        # Prefer UNIX domain sockets over TCP sockets
        config.scgi_url = config.scgi_local or config.scgi_port


    def __repr__(self):
        """ Return a representation of internal state.
        """
        if self._rpc:
            # Connected state
            return "%s connected to %s [%s] via %r" % (
                self.__class__.__name__, self.engine_id, self.engine_software, config.scgi_url,
            )
        else:
            # Unconnected state
            self._load_rtorrent_rc(config)
            return "%s connectable via %r" % (
                self.__class__.__name__, config.scgi_url,
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
        self._rpc = xmlrpc2scgi.RTorrentXMLRPCClient(config.scgi_url)
        try:
            self.engine_id = self._rpc.get_name()
            time_usec = self._rpc.system.time_usec()
        except socket.error, exc:
            raise error.LoggableError("Can't connect to %s (%s)" % (config.scgi_url, exc))
        except Exception, exc:
            raise error.LoggableError("Can't connect to %s (%s)" % (config.scgi_url, exc))

        # Make sure xmlrpc-c works as expected
        if type(time_usec) is not long:
            self.LOG.warn("Your xmlrpc-c is broken (64 bit integer support missing,"
                " %r returned instead)" % (type(time_usec),))

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
