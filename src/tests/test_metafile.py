# -*- coding: utf-8 -*-
# pylint: disable=
""" Metafile tests.

    Copyright (c) 2009 The PyroScope Project <pyroscope.project@gmail.com>

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

import random
import logging
import unittest

from pyrocore.util.metafile import * #@UnusedWildImport

log = logging.getLogger(__name__)
log.trace("module loaded")


class MaskTest(unittest.TestCase):

    def test_urls(self):
        testcases = (
            "http://example.com:1234/user/ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ/announce",
            "http://example.com/announce.php?passkey=ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
            "http://example.com/announce.php?passkey=ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ&someparam=0",
            "http://example.com/DDDDD/ZZZZZZZZZZZZZZZZ/announce",
            "http://example.com/tracker.php/ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ/announce",
            "https://example.com/announce.php?passkey=ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
            "http://tracker1.example.com/TrackerServlet/ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ/DDDDDDD/announce",
            "http://example.com:12345/ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ/announce",
            "http://example.com/announce.php?pid=ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
            "http://example.com:1234/a/ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ/announce",
            "http://example.com/announce.php?passkey=ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ&uid=DDDDD",
        )
        mapping = {
            "D": lambda: random.choice("0123456789"),
            "Z": lambda: random.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"),
        }

        for testcase in testcases:
            expected = testcase.replace("D", "*").replace("Z", "*")
            randomized = ''.join(mapping.get(i, lambda: i)() for i in testcase)
            print expected, randomized
            self.failIfEqual(expected, randomized)
            self.failUnlessEqual(expected, mask_keys(randomized))

if __name__ == "__main__":
    unittest.main()
