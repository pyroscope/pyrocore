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
import copy
import operator
from functools import reduce  # forward compatibility for Python 3

from pyrocore.util.metafile import * #@UnusedWildImport
from pyrobase.bencode import bread

log = logging.getLogger(__name__)
log.trace("module loaded")

# helper methods to make tests easier to write
def get_from_dict(data_dict, map_list):
    return reduce(operator.getitem, map_list, data_dict)
def set_in_dict(data_dict, map_list, value):
    get_from_dict(data_dict, map_list[:-1])[map_list[-1]] = value


class MaskTest(unittest.TestCase):

    def test_urls(self):
        testcases = (
            u"http://example.com:1234/user/ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ/announce",
            u"http://example.com/announce.php?passkey=ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
            u"http://example.com/announce.php?passkey=ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ&someparam=0",
            u"http://example.com/DDDDD/ZZZZZZZZZZZZZZZZ/announce",
            u"http://example.com/tracker.php/ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ/announce",
            u"https://example.com/announce.php?passkey=ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
            u"http://tracker1.example.com/TrackerServlet/ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ/DDDDDDD/announce",
            u"http://example.com:12345/ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ/announce",
            u"http://example.com/announce.php?pid=ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
            u"http://example.com:1234/a/ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ/announce",
            u"http://example.com/announce.php?passkey=ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ&uid=DDDDD",
        )
        mapping = {
            "D": lambda: random.choice("0123456789"),
            "Z": lambda: random.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYabcdefghijklmnopqrstuvwxyz"),
        }

        for testcase in testcases:
            expected = testcase.replace("D", "*").replace("Z", "*")
            randomized = ''.join(mapping.get(i, lambda: i)() for i in testcase)
            self.assertNotEqual(expected, randomized)
            self.assertEqual(expected, mask_keys(randomized))

class AssignTest(unittest.TestCase):
    def test_assign_fields(self):
        # 4-elem tuples: initial, key, value, expected
        tests = [
            (
                {},
                "test",
                "test",
                {"test", "test"}
            ),
        ]
        for initial, key, value, expected in tests:
            continue
            self.assertEqual(initial)

class CheckMetaTest(unittest.TestCase):
    def test_metadicts(self):
        bad_dicts = [
            ['a'],
            {'agsdg': 'asdga'},
            {'announce', 3},
        ]
        for testcase in bad_dicts:
            self.failUnlessRaises(ValueError, check_meta, testcase)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        good_metainfo = bread(os.path.join(dir_path, 'multi.torrent'))
        bad_meta_info_data = [
            ([], ['a']),
            (['pieces'], u"test"),
            (['piece length'], -1),
            (['name'], 5),
            (['name'], '/tmp/file'),
            (['length'], good_metainfo['info']['files']),
            (['length'], -1),
            (['files'], 1),
            (['files'], [1]),
            (['files'], [{'length': -1}]),
            (['files'], [{'length': 1, 'path': -1}]),
            (['files'], [{'length': 1, 'path': -1}]),
            (['files'], [{'length': 1, 'path': [-1]}]),
            (['files'], [{'length': 1, 'path': [u'file', u'/tmp/file']}]),
            (['files'], [{'length': 1, 'path': [u'..', u'file']}]),
            (['files'], [
                {'length': 1, 'path': [u'file']},
                {'length': 1, 'path': [u'file']},
            ]),
        ]
        for key, data in bad_meta_info_data:
            meta = copy.deepcopy(good_metainfo)
            set_in_dict(meta, ['info'] + key, data)
            print(meta)
            self.failUnlessRaises(ValueError, check_meta, meta)

        self.assertEqual(good_metainfo, check_meta(good_metainfo))

if __name__ == "__main__":
    unittest.main()
