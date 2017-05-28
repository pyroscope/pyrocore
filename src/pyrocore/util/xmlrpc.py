# -*- coding: utf-8 -*-
# pylint: disable=I0011,W0212
""" RTorrent client proxy.

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
from __future__ import absolute_import

import sys
import time
import xmlrpclib

from pyrobase.io import xmlrpc2scgi

from pyrocore import config, error
from pyrocore.util import os, fmt, pymagic


NOHASH = ''  # use named constant to make new-syntax commands with no hash easily searchable


class XmlRpcError(Exception):
    """Base class for XMLRPC protocol errors."""

    def __init__(self, msg, *args):
        Exception.__init__(self, msg, *args)
        self.message = msg.format(*args)
        self.faultString = self.message
        self.faultCode = -500

    def __str__(self):
        return self.message


class HashNotFound(XmlRpcError):
    """Non-existing or disappeared hash."""

    def __init__(self, msg, *args):
        XmlRpcError.__init__(self, msg, *args)
        self.faultCode = -404


# Currently, we don't have our own errors, so just copy it
ERRORS = (XmlRpcError,) + xmlrpc2scgi.ERRORS


class RTorrentMethod(object):
    """ Collect attribute accesses to build the final method name.
    """

    # Actually, many more methods might need a fake target added; but these are the ones we call...
    NEEDS_FAKE_TARGET = set((
        "ui.current_view.set",
        "view_filter",
    ))


    def __init__(self, proxy, method_name):
        self._proxy = proxy
        self._method_name = method_name


    def __getattr__(self, attr):
        """ Append attr to the existing method name.
        """
        self._method_name += '.' + attr
        return self


    def __str__(self):
        """ Return statistics for this call.
        """
        return "out %s, in %s, took %.3fms/%.3fms" % (
            fmt.human_size(self._outbound).strip(),
            fmt.human_size(self._inbound).strip(),
            self._net_latency * 1000.0,
            self._latency * 1000.0,
        )


    def __call__(self, *args, **kwargs):
        """ Execute the method call.

            `raw_xml=True` returns the unparsed XML-RPC response.
            `flatten=True` removes one nesting level in a result list (useful for multicalls).
        """
        self._proxy._requests += 1
        start = time.time()
        raw_xml = kwargs.get("raw_xml", False)
        flatten = kwargs.get("flatten", False)
        fail_silently = kwargs.get("fail_silently", False)

        try:
            # Map multicall arguments
            if not self._proxy._use_deprecated:
                if self._method_name.endswith(".multicall") or self._method_name.endswith(".multicall.filtered"):
                    if self._method_name in ("d.multicall", "d.multicall.filtered"):
                        args = (0,) + args
                    if config.debug:
                        self._proxy.LOG.debug("BEFORE MAPPING: %r" % (args,))
                    if self._method_name == "system.multicall":
                        for call in args[0]:
                            call["methodName"] = self._proxy._map_call(call["methodName"])
                    else:
                        args = args[0:2] + tuple(self._proxy._map_call(i) for i in args[2:])
                    if config.debug:
                        self._proxy.LOG.debug("AFTER MAPPING: %r" % (args,))
                elif self._method_name in self.NEEDS_FAKE_TARGET:
                    args = (0,) + args

            # Prepare request
            xmlreq = xmlrpclib.dumps(args, self._proxy._map_call(self._method_name))
            ##xmlreq = xmlreq.replace('\n', '')
            self._outbound = len(xmlreq)
            self._proxy._outbound += self._outbound
            self._proxy._outbound_max = max(self._proxy._outbound_max, self._outbound)

            if config.debug:
                self._proxy.LOG.debug("XMLRPC raw request: %r" % xmlreq)

            # Send it
            scgi_req = xmlrpc2scgi.SCGIRequest(self._proxy._transport)
            xmlresp = scgi_req.send(xmlreq)
            self._inbound = len(xmlresp)
            self._proxy._inbound += self._inbound
            self._proxy._inbound_max = max(self._proxy._inbound_max, self._inbound)
            self._net_latency = scgi_req.latency
            self._proxy._net_latency += self._net_latency

            # Return raw XML response?
            if raw_xml:
                return xmlresp

            # This fixes a bug with the Python xmlrpclib module
            # (has no handler for <i8> in some versions)
            xmlresp = xmlresp.replace("<i8>", "<i4>").replace("</i8>", "</i4>")

            try:
                # Deserialize data
                result = xmlrpclib.loads(xmlresp)[0][0]
            except (KeyboardInterrupt, SystemExit):
                # Don't catch these
                raise
            except:
                exc_type, exc = sys.exc_info()[:2]
                if exc_type is xmlrpclib.Fault and exc.faultCode == -501 and exc.faultString == 'Could not find info-hash.':
                    raise HashNotFound("Unknown hash for {}({}) @ {}", self._method_name, args[0] if args else '', self._proxy._url)

                if not fail_silently:
                    # Dump the bad packet, then re-raise
                    filename = "/tmp/xmlrpc2scgi-%s.xml" % os.getuid()
                    handle = open(filename, "w")
                    try:
                        handle.write("REQUEST\n")
                        handle.write(xmlreq)
                        handle.write("\nRESPONSE\n")
                        handle.write(xmlresp)
                        print >>sys.stderr, "INFO: Bad data packets written to %r" % filename
                    finally:
                        handle.close()
                raise
            else:
                try:
                    return sum(result, []) if flatten else result
                except TypeError:
                    if result and isinstance(result, list) and isinstance(result[0], dict) and 'faultCode' in result[0]:
                        raise error.LoggableError("XMLRPC error in multicall: " + repr(result[0]))
                    else:
                        raise
        finally:
            # Calculate latency
            self._latency = time.time() - start
            self._proxy._latency += self._latency

            if config.debug:
                self._proxy.LOG.debug("%s(%s) took %.3f secs" % (
                    self._method_name,
                    ", ".join(repr(i) for i in args),
                    self._latency
                ))


class RTorrentProxy(object):
    """ Proxy to rTorrent's XMLRPC interface.

        Method calls are built from attribute accesses, i.e. you can do
        something like C{proxy.system.client_version()}.
    """

    def __init__(self, url, mapping=None):
        self.LOG = pymagic.get_class_logger(self)
        self._url = url
        self._transport = xmlrpc2scgi.transport_from_url(url)
        self._versions = ("", "")
        self._version_info = ()
        self._use_deprecated = True
        self._mapping = mapping or config.xmlrpc
        self._fix_mappings()

        # Statistics (traffic w/o HTTP overhead)
        self._requests = 0
        self._outbound = 0
        self._outbound_max = 0
        self._inbound = 0
        self._inbound_max = 0
        self._latency = 0.0
        self._net_latency = 0.0


    def __str__(self):
        """ Return statistics.
        """
        return "%d req, out %s [%s max], in %s [%s max], %.3fms/%.3fms avg latency" % (
            self._requests,
            fmt.human_size(self._outbound).strip(),
            fmt.human_size(self._outbound_max).strip(),
            fmt.human_size(self._inbound).strip(),
            fmt.human_size(self._inbound_max).strip(),
            self._net_latency * 1000.0 / self._requests,
            self._latency * 1000.0 / self._requests,
        )


    def _set_mappings(self):
        """ Set command mappings according to rTorrent version.
        """
        try:
            self._versions = (self.system.client_version(), self.system.library_version(),)
            self._version_info = tuple(int(i) for i in self._versions[0].split('.'))
            self._use_deprecated = self._version_info < (0, 8, 7)

            # Merge mappings for this version
            self._mapping = self._mapping.copy()
            for key, val in sorted(i for i in vars(config).items() if i[0].startswith("xmlrpc_")):
                map_version = tuple(int(i) for i in key.split('_')[1:])
                if map_version <= self._version_info:
                    if config.debug:
                        self.LOG.debug("MAPPING for %r added: %r" % (map_version, val))
                    self._mapping.update(val)
            self._fix_mappings()
        except ERRORS as exc:
            raise error.LoggableError("Can't connect to %s (%s)" % (self._url, exc))

        return self._versions, self._version_info


    def _fix_mappings(self):
        """ Add computed stuff to mappings.
        """
        self._mapping.update((key+'=', val+'=') for key, val in self._mapping.items() if not key.endswith('='))

        if config.debug:
            self.LOG.debug("CMD MAPPINGS ARE: %r" % (self._mapping,))


    def _map_call(self, cmd):
        """ Map old to new command names.
        """
        if config.debug and cmd != self._mapping.get(cmd, cmd):
            self.LOG.debug("MAP %s ==> %s" % (cmd, self._mapping[cmd]))
        cmd = self._mapping.get(cmd, cmd)

        # These we do by code, to avoid lengthy lists in the config
        if not self._use_deprecated and any(cmd.startswith(i) for i in ("d.get_", "f.get_", "p.get_", "t.get_")):
            cmd = cmd[:2] + cmd[6:]

        return cmd


    def __getattr__(self, attr):
        """ Return a method object for accesses to virtual attributes.
        """
        return RTorrentMethod(self, attr)


    def __repr__(self):
        """ Return info & statistics.
        """
        return "%s(%r) [%s]" % (self.__class__.__name__, self._url, self)
