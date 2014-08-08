# -*- coding: utf-8 -*-
# pylint: disable=I0011
""" Statistics data.

    Copyright (c) 2014 The PyroScope Project <pyroscope.project@gmail.com>
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

import time


def engine_data(engine):
    """ Get important performance data and metadata from rTorrent.
    """
    views = ("main", "started", "stopped", "complete", "incomplete", "seeding", "leeching", "active", "messages")
    methods = [
        "get_up_rate", "get_upload_rate",
        "get_down_rate", "get_download_rate",
    ]

    # Get data via multicall
    proxy = engine.open()
    calls = [dict(methodName=method, params=[]) for method in methods] \
          + [dict(methodName="view.size", params=['', view]) for view in views]
    result = proxy.system.multicall(calls, flatten=True)

    # Build result object
    data = dict(
        now         = time.time(),
        engine_id   = engine.engine_id,
        versions    = engine.versions,
        uptime      = engine.uptime,
        upload      = [result[0], result[1]],
        download    = [result[2], result[3]],
        views       = dict([(name, result[4+i])
            for i, name in enumerate(views)
        ]),
    )

    return data
