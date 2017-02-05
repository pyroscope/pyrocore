# -*- coding: utf-8 -*-
# pylint: disable=
""" Torrent Engine tests.

    Copyright (c) 2011 The PyroScope Project <pyroscope.project@gmail.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
import logging
import unittest

from pyrocore.torrent import engine

log = logging.getLogger(__name__)
log.trace("module loaded")


class IntervalTest(unittest.TestCase):

    INTERVAL_DATA = [
        ("R1377390013R1377390082", dict(end=1377390084), 2),
        ("R1353618135P1353618151", dict(start=1353618141), 10),
    ]

    def test_interval_sum(self):
        for context in (None, "unittest"):
            for interval, kwargs, expected in self.INTERVAL_DATA:
                kwargs["context"] = context
                result = engine._interval_sum(interval, **kwargs)
                self.assertEqual(expected, result, "for interval=%r kw=%r" % (interval, kwargs))


class EngineTest(unittest.TestCase):

    def test_engine(self):
        pass


if __name__ == "__main__":
    unittest.main()
