# -*- coding: utf-8 -*-
# pylint: disable=bad-whitespace
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
from __future__ import absolute_import

from pyrocore import error
from pyrocore.util import xmlrpc

def engine_data(engine):
    """ Get important performance data and metadata from rTorrent.
    """
    proxy = engine.open()
    views = proxy.view.list()

    methods = [
        "throttle.global_up.rate", "throttle.global_up.max_rate",
        "throttle.global_down.rate", "throttle.global_down.max_rate",
        "pieces.stats_not_preloaded", "pieces.stats_preloaded",
        "system.files.opened_counter", "system.files.failed_counter", "system.files.closed_counter",
        "pieces.memory.block_count", "pieces.memory.current",
        "network.open_sockets"
    ]

    # Get data via multicall
    calls = [dict(methodName=method, params=[]) for method in methods] \
          + [dict(methodName="view.size", params=['', view]) for view in views]
    result = proxy.system.multicall(calls, flatten=True)
    result_dict = {}
    for m in methods:
        result_dict[m] = result[0]
        del result[0]
    result_dict['views'] = {}
    for v in views:
        result_dict['views'][v] = {}
        result_dict['views'][v]['size'] = result[0]
        del result[0]
    return result_dict

def module_test():
    """ Quick test using…

            python -m pyrocore.util.stats
    """
    import pprint
    from pyrocore import connect

    try:
        engine = connect()
        print("%s - %s" % (engine.engine_id, engine.open()))

        result = engine_data(engine)
        print "result = ",
        pprint.pprint(result)

        print("%s - %s" % (engine.engine_id, engine.open()))
    except (error.LoggableError, xmlrpc.ERRORS), torrent_exc:
        print("ERROR: %s" % torrent_exc)


if __name__ == "__main__":
    module_test()
