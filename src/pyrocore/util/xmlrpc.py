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
import sys
import time
import xmlrpclib

from pyrobase.io import xmlrpc2scgi

from pyrocore import config
from pyrocore.util import os, fmt, pymagic


class RTorrentMethod(object):
    """ Collect attribute accesses to build the final method name.
    """

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
        """
        self._proxy._requests += 1
        start = time.time()
        raw_xml = kwargs.get("raw_xml", False)

        try:
            # Prepare request
            xmlreq = xmlrpclib.dumps(args, config.xmlrpc.get(self._method_name, self._method_name))
            self._outbound = len(xmlreq)
            self._proxy._outbound += self._outbound
            self._proxy._outbound_max = max(self._proxy._outbound_max, self._outbound) 

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
                # Return deserialized data
                return xmlrpclib.loads(xmlresp)[0][0]
            except (KeyboardInterrupt, SystemExit):
                # Don't catch these
                raise
            except:
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
    
    def __init__(self, url):
        self.LOG = pymagic.get_class_logger(self)
        self._url = url
        self._transport = xmlrpc2scgi.transport_from_url(url)

        # Statistics (traffic w/o HTTP overhead)
        self._requests = 0
        self._outbound = 0L
        self._outbound_max = 0L
        self._inbound = 0L
        self._inbound_max = 0L
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


    def __getattr__(self, attr):
        """ Return a method object for accesses to virtual attributes.
        """
        return RTorrentMethod(self, attr)


    def __repr__(self):
        """ Return info & statistics.
        """
        return "%s(%r) [%s]" % (self.__class__.__name__, self._url, self)
