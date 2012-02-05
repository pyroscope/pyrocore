# -*- coding: utf-8 -*-
# pylint: disable=I0011
""" rTorrent Queue Manager.

    Copyright (c) 2012 The PyroScope Project <pyroscope.project@gmail.com>
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
from __future__ import with_statement

import operator

from pyrocore import error, config
from pyrocore.util import os, fmt, xmlrpc, pymagic


class QueueManager(object):
    """ rTorrent queue manager implementation.
    """
    VIEWNAME = "pyrotorque"


    def __init__(self, config=None):
        """ Set up queue manager.
        """
        self.config = config or {}
        self.LOG = pymagic.get_class_logger(self)
        self.LOG.info("Queue manager created with config %r" % self.config)


    def _start(self, items):
        """ Start some items if conditions are met.
        """
        # Check if anything more can be downloading at all
        startable = [i for i in items if not (i.is_open or i.is_active or i.is_ignored or i.is_complete)]
        if not startable:
            self.LOG.debug("Checked %d item(s), none startable" % (len(items),))
            return

        # Stick to "start_at_once" parameter, unless "downloading_min" is violated
        downloading = [i for i in items if i.is_active and not i.is_complete]
        start_now = max(self.config.start_at_once, self.config.downloading_min - len(downloading))
        start_now = min(start_now, len(startable))

        #down_traffic = sum(i.down for i in downloading)
        ##self.LOG.info("%d downloading, down %d" % (len(downloading), down_traffic))
        
        # Start eligible items
        for idx, item in enumerate(startable):
            # Check if we reached 'start_now' in this run
            if idx >= start_now:
                self.LOG.debug("Only starting %d item(s) in this run, %d more could be downloading" % (
                    start_now, len(startable)-idx,))
                break

            # Only check the other conditions when we have `downloading_min` covered
            if len(downloading) < self.config.downloading_min:
                self.LOG.debug("Catching up from %d to a minimum of %d downloading item(s)" % (
                    len(downloading), self.config.downloading_min))
            else:
                # Limit to the given maximum of downloading items
                if len(downloading) >= self.config.downloading_max:
                    self.LOG.debug("Already downloading %d item(s) out of %d max, %d more could be downloading" % (
                        len(downloading), self.config.downloading_max, len(startable)-idx,))
                    break

            # If we made it here, start it!
            downloading.append(item)
            self.LOG.info("%s '%s' [%s, #%s]" % (
                "WOULD start" if self.config.dry_run else "Starting", 
                fmt.to_utf8(item.name), item.alias, item.hash))
            if not self.config.dry_run:
                item.start()


    def run(self):
        """ Queue manager job callback.
        """
        try:
            proxy = config.engine.open()
            
            # Get items from 'pyrotorque' view
            items = list(config.engine.items(self.VIEWNAME, cache=False))
            items.sort(key=operator.attrgetter("loaded", "name"))

            # Handle found items
            self._start(items)
        except (error.LoggableError, xmlrpc.ERRORS), exc:
            # only debug, let the statistics logger do its job
            self.LOG.debug(str(exc)) 

