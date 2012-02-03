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

from pyrocore import error, config
from pyrocore.util import os, pymagic


class QueueManager(object):
    """ rTorrent queue manager implementation.
    """

    def __init__(self, config=None):
        """ Set up queue manager.
        """
        self.config = config or {}
        self.LOG = pymagic.get_class_logger(self)
        self.LOG.info("Queue manager created with config %r" % self.config)


    def run(self):
        """ The job callback.
        """
        self.LOG.info("Queue manager run")

