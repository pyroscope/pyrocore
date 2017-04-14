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
from __future__ import absolute_import

import time

from pyrocore import error
from pyrocore import config as config_ini
from pyrocore.util import fmt, xmlrpc, pymagic
from pyrocore.torrent import engine, matching, formatting


class QueueManager(object):
    """ rTorrent queue manager implementation.
    """
    # Special view containing all items that are transferring data, have peers connected, or are incomplete
    VIEWNAME = "pyrotorque"


    def __init__(self, config=None):
        """ Set up queue manager.
        """
        self.config = config or {}
        self.proxy = None
        self.last_start = 0
        self.LOG = pymagic.get_class_logger(self)
        self.LOG.debug("Queue manager created with config %r" % self.config)

        bool_param = lambda key, default: matching.truth(self.config.get(key, default), "job.%s.%s" % (self.config.job_name, key))

        self.config.quiet = bool_param("quiet", False)
        self.config.startable = matching.ConditionParser(engine.FieldDefinition.lookup, "name").parse(
            "is_open=0 is_active=0 is_complete=0 [ %s ]" % self.config.startable
        )
        self.LOG.info("Startable matcher for '%s' is: [ %s ]" % (self.config.job_name, self.config.startable))
        self.config.downloading = matching.ConditionParser(engine.FieldDefinition.lookup, "name").parse(
            "is_active=1 is_complete=0" + (" [ %s ]" % self.config.downloading if "downloading" in self.config else "")
        )
        self.LOG.info("Downloading matcher for '%s' is: [ %s ]" % (self.config.job_name, self.config.downloading))
        self.sort_key = formatting.validate_sort_fields(self.config.sort_fields) if self.config.sort_fields.strip() else None


    def _start(self, items):
        """ Start some items if conditions are met.
        """
        # TODO: Filter by a custom date field, for scheduled downloads starting at a certain time, or after a given delay

        # TODO: Don't start anything more if download BW is used >= config threshold in %

        # Check if anything more is ready to start downloading
        startable = [i for i in items if self.config.startable.match(i)]
        if not startable:
            self.LOG.debug("Checked %d item(s), none startable" % (len(items),))
            return

        # Check intermission delay
        now = time.time()
        if now < self.last_start:
            # compensate for summer time and other oddities
            self.last_start = now
        delayed = int(self.last_start + self.config.intermission - now)
        if delayed > 0:
            self.LOG.debug("Delaying start of {:d} item(s),"
                           " due to {:d}s intermission with {:d}s left"
                           .format(len(startable), self.config.intermission, delayed))
            return

        # TODO: sort by priority, then loaded time

        # Stick to "start_at_once" parameter, unless "downloading_min" is violated
        downloading = [i for i in items if self.config.downloading.match(i)]
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

            # TODO: Prevent start of more torrents that can fit on the drive (taking "off" files into account)
            # (restarts items that were stopped due to the "low_diskspace" schedule, and also avoids triggering it at all)

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
            self.last_start = now
            downloading.append(item)
            self.LOG.info("%s '%s' [%s, #%s]" % (
                "WOULD start" if self.config.dry_run else "Starting",
                fmt.to_utf8(item.name), item.alias, item.hash))
            if not self.config.dry_run:
                item.start()
                if not self.config.quiet:
                    self.proxy.log(xmlrpc.NOHASH, "%s: Started '%s' {%s}" % (
                        self.__class__.__name__, fmt.to_utf8(item.name), item.alias,
                    ))


    def run(self):
        """ Queue manager job callback.
        """
        try:
            self.proxy = config_ini.engine.open()

            # Get items from 'pyrotorque' view
            items = list(config_ini.engine.items(self.VIEWNAME, cache=False))

            if self.sort_key:
                items.sort(key=self.sort_key)
                #self.LOG.debug("Sorted: %r" % [i.name for i in items])

            # Handle found items
            self._start(items)
            self.LOG.debug("%s - %s" % (config_ini.engine.engine_id, self.proxy))
        except (error.LoggableError, xmlrpc.ERRORS) as exc:
            # only debug, let the statistics logger do its job
            self.LOG.debug(str(exc))
