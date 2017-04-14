# -*- coding: utf-8 -*-
# pylint: disable=I0011
""" rTorrent Item Filter Jobs.

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
from __future__ import absolute_import

from pyrocore import error
from pyrocore.util import xmlrpc, pymagic


class FilterJobBase(object):
    """ Base class for filter rule jobs.
    """

    def __init__(self, config=None):
        """ Set up filter config.
        """
        self.config = config or {}
        self.LOG = pymagic.get_class_logger(self)
        self.LOG.debug("%s created with config %r" % (self.__class__.__name__, self.config))


    def run(self):
        """ Filter job callback.
        """
        from pyrocore import config

        try:
            config.engine.open()
            # TODO: select view into items
            items = []
            self.run_filter(items)
        except (error.LoggableError, xmlrpc.ERRORS) as exc:
            self.LOG.warn(str(exc))


    def run_filter(self, items):
        """ Perform job on filtered items.
        """
        raise NotImplementedError()


class ActionRule(FilterJobBase):
    """ Perform an action on selected items.
    """

    def run_filter(self, items):
        """ Perform configured action on filtered items.
        """
        # TODO: what actions? xmlrpc, delete, cull, stop, etc. for sure.


class TorrentMirror(FilterJobBase):
    """ Mirror selected items via a specified tracker.
    """

    def run_filter(self, items):
        """ Load filtered items into remote client via tracker / watchdir.
        """
        # TODO: config is tracker_url, tracker_upload, watch_dir
        # create clones of item's metafile, write to watch_dir, and upload
        # to tracker_upload (support file: at first, for a local bttrack);
        # also, already mirrored items have to be marked somehow
