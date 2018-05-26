# -*- coding: utf-8 -*-
# pylint: disable=I0011,C0103
""" rTorrent Disk Space House-Keeping.

    This is used in the ``rtsweep`` tool and the queue job of the
    ``pyrotoque`` daemon to free up disk space for new items, by
    deleting old items in a controlled way using a configurable order.

    Copyright (c) 2018 The PyroScope Project <pyroscope.project@gmail.com>
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

from pyrocore import config
from pyrocore.torrent import matching
