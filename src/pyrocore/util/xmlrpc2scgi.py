#!/usr/bin/env python

# Copyright (C) 2005-2007, Glenn Washburn
#
# Refactoring - Copyright (c) 2010 The PyroScope Project <pyroscope.project@gmail.com>
#
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# In addition, as a special exception, the copyright holders give
# permission to link the code of portions of this program with the
# OpenSSL library under certain conditions as described in each
# individual source file, and distribute linked combinations
# including the two.
#
# You must obey the GNU General Public License in all respects for
# all of the code used other than OpenSSL.  If you modify file(s)
# with this exception, you may extend this exception to your version
# of the file(s), but you are not obligated to do so.  If you do not
# wish to do so, delete this exception statement from your version.
# If you delete this exception statement from all source files in the
# program, then also delete it here.
#
# Contact:  Glenn Washburn <crass@berlios.de>
#
# Note that, before you contact the original author, this version of
# the module has undergone extensive refactoring.
#

import os
import sys
import time
import socket
import urllib
import urlparse
import xmlrpclib

from pyrocore import config
from pyrocore.util import fmt

# this allows us to parse scgi urls just like http ones
from urlparse import uses_netloc
uses_netloc.append('scgi')
del uses_netloc


def do_scgi_xmlrpc_request(host, methodname, params=()):
    """
        Send an xmlrpc request over scgi to host.
        host:       scgi://host:port/path
        methodname: xmlrpc method name
        params:     tuple of simple python objects
        returns:    xmlrpc response
    """
    xmlreq = xmlrpclib.dumps(params, methodname)
    xmlresp = SCGIRequest(host).send(xmlreq)
    #~ print xmlresp
    
    return xmlresp


def do_scgi_xmlrpc_request_py(host, methodname, params=()):
    """
        Send an xmlrpc request over scgi to host.
        host:       scgi://host:port/path
        methodname: xmlrpc method name
        params:     tuple of simple python objects
        returns:    xmlrpc response converted to python
    """
    xmlresp = do_scgi_xmlrpc_request(host, methodname, params)
    return xmlrpclib.loads(xmlresp)[0][0]


class SCGIRequest(object):
    """ See spec at: http://python.ca/scgi/protocol.txt
        Send an SCGI request.
        
        Use tcp socket
        SCGIRequest('scgi://host:port').send(data)
        
        Or use the named unix domain socket
        SCGIRequest('scgi:///tmp/rtorrent.sock').send(data)
    """

    # Amount of bytes to read at once
    CHUNK_SIZE = 32768

    
    def __init__(self, url):
        self.url = url
        self.resp_headers = []
        self.latency = 0.0

    
    def __send(self, scgireq):
        # Parse endpoint URL
        _, netloc, path, _, _ = urlparse.urlsplit(self.url)
        host, port = urllib.splitport(netloc)
        #~ print '>>>', (netloc, host, port)

        # Connect to the specified endpoint
        start = time.time()
        if netloc:
            addrinfo = list(set(socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)))
            
            assert len(addrinfo) == 1, "There's more than one? %r"%addrinfo
            #~ print addrinfo
            
            sock = socket.socket(*addrinfo[0][:3])
            sock.connect(addrinfo[0][4])
        else:
            # If no host then assume unix domain socket
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                sock.connect(path)
            except socket.error, exc:
                raise socket.error("Can't connect to %r (%s)" % (path, exc))

        try:
            # Send request        
            sock.send(scgireq)

            # Read response
            resp = []
            while True:
                chunk = sock.recv(self.CHUNK_SIZE)
                if chunk:
                    resp.append(chunk)
                else:
                    break
        finally:
            # Clean up
            sock.close()
            self.latency = time.time() - start
        
        # Return result
        # (note that this returns resp unchanged for lists of length 1 in CPython)
        return ''.join(resp)

    
    def send(self, data):
        """ Send data over scgi to URL and get response.
        """
        scgiresp = self.__send(self.add_required_scgi_headers(data))
        resp, self.resp_headers = self.get_scgi_resp(scgiresp)

        return resp

    
    @staticmethod
    def encode_netstring(string):
        "Encode string as netstring"
        return '%d:%s,' % (len(string), string)

    
    @staticmethod
    def make_headers(headers):
        "Make scgi header list"
        return '\x00'.join(['%s\x00%s' % t for t in headers]) + '\x00'
    

    @staticmethod
    def add_required_scgi_headers(data, headers=[]):
        """ Wrap data in an scgi request,
            see spec at: http://python.ca/scgi/protocol.txt
        """
        # See spec at: http://python.ca/scgi/protocol.txt
        headers = SCGIRequest.make_headers([
            ('CONTENT_LENGTH', str(len(data))),
            ('SCGI', '1'),
        ] + headers)
        
        enc_headers = SCGIRequest.encode_netstring(headers)
        
        return enc_headers + data
    

    @staticmethod
    def parse_headers(headers):
        """ Get header (key, value) pairs from header string.
        """
        return [line.rstrip().split(": ", 1)
            for line in headers.splitlines()
        ]

    
    @staticmethod
    def get_scgi_resp(resp):
        """ Get xmlrpc response from scgi response
        """
        # Assume they care for standards and send us CRLF (not just LF)
        headers, payload = resp.split("\r\n\r\n", 1)

        return payload, SCGIRequest.parse_headers(headers)


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


    def __call__(self, *args):
        """ Execute the method call.
        """
        self._proxy._requests += 1
        start = time.time()

        try:
            # Prepare request
            xmlreq = xmlrpclib.dumps(args, config.xmlrpc.get(self._method_name, self._method_name))
            self._outbound = len(xmlreq)
            self._proxy._outbound += self._outbound

            # Send it
            scgi_req = SCGIRequest(self._proxy._url)
            xmlresp = scgi_req.send(xmlreq)
            self._inbound = len(xmlresp)
            self._proxy._inbound += self._inbound
            self._net_latency = scgi_req.latency
            self._proxy._net_latency += self._net_latency
            
            # This fixes a bug with the Python xmlrpclib module
            # (has no handler for <i8> in some versions)
            xmlresp = xmlresp.replace("<i8>", "<i4>").replace("</i8>", "</i4>")

            try:
                # Return deserialized data
                return xmlrpclib.loads(xmlresp)[0][0]
                #~ return do_scgi_xmlrpc_request_py(self._proxy._url, self.method_name, args)
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


class RTorrentProxy(object):
    """
    The following is an example of how to use this class.
    rtorrent_host='http://localhost:33000'
    rtc = RTorrentProxy(rtorrent_host)
    for infohash in rtc.download_list('complete'):
        if rtc.d.get_ratio(infohash) > 500:
            print "%s has a ratio of over 0.5"%(rtc.d.get_name(infohash))
    """
    
    def __init__(self, url):
        self._url = url

        # Statistics (traffic w/o HTTP overhead)
        self._requests = 0
        self._outbound = 0L
        self._inbound = 0L
        self._latency = 0.0
        self._net_latency = 0.0

        # TODO: Should also support "host:port" and "socket_path"
        scheme, _, _, _, _ = urlparse.urlsplit(self._url)
        assert scheme == 'scgi', 'Unsupported protocol'

    
    def __str__(self):
        """ Return statistics.
        """
        return "%d req, out %s, in %s, %.3fms/%.3fms avg latency" % (
            self._requests, 
            fmt.human_size(self._outbound).strip(), 
            fmt.human_size(self._inbound).strip(), 
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


def convert_params_to_native(params):
    """ Parse xmlrpc-c command line arg syntax.
    """
    #~ print 'convert_params_to_native', params
    cparams = []
    # parse parameters
    for param in params:
        if len(param) < 2 or param[1] != '/':
            cparams.append(param)
            continue
        
        if param[0] == 'i':
            ptype = int
        elif param[0] == 'b':
            ptype = bool
        elif param[0] == 's':
            ptype = str
        else:
            cparams.append(param)
            continue
        
        cparams.append(ptype(param[2:]))
    
    return tuple(cparams)


def main(argv):
    """ Command line handler.
    """
    output_python = False
    
    if argv[0] == '-p':
        output_python=True
        argv.pop(0)
    
    host, methodname = argv[:2]
    
    respxml = do_scgi_xmlrpc_request(host, methodname, convert_params_to_native(argv[2:]))
    ##respxml = RTorrentProxy(host, methodname)(convert_params_to_native(argv[2:]))
    
    if not output_python:
        print respxml
    else:
        print xmlrpclib.loads(respxml)[0][0]


if __name__ == "__main__":
    main(sys.argv[1:])
