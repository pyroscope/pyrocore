""" PyroCore - Filter condition tests.

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

from pyrocore.util import matching
from pyrocore.util.types import Bunch

log = logging.getLogger(__name__)
log.trace("module loaded")


def lookup(name):
    """ Lookup for test fields.
    """
    matchers = dict(
        name = matching.GlobFilter,
        num = matching.FloatFilter,
        flag = matching.BoolFilter,
    )
    return {"matcher": matchers[name]} if name in matchers else None


class FilterTest(unittest.TestCase):
    DATA = [
        Bunch(name="T1", num=1, flag=True),
        Bunch(name="F0", num=0, flag=False),
        Bunch(name="T11", num=11, flag=True),
    ]
    CASES = [
        ("flag=y", "T1 T11"),
        ("num=-1", "F0"),
        ("num=-2", "F0 T1"),
        ("num=+99", ""),
        ("T?", "T1"),
        ("T*", "T1 T11"),
    ]

    def test_conditions(self):
        for cond, expected in self.CASES:
            keep = matching.ConditionParser(lookup, "name").parse(cond)
            result = set(i.name for i in self.DATA if keep(i))
            expected = set(expected.split())
            assert result == expected, "Expected %r, but got %r" % (expected, result) 


class ParserTest(unittest.TestCase):
    GOOD = [
        "num=+1",
        "flag=y",
        "some*name",
    ]
    BAD = [
        "num=foo",
        "flag=foo",
        "unknown=",
        "no field name",
        "[ num=1",
        # TODO: "num=1 ]",
        "num=1 OR OR flag=1",
        "num=1 OR",
        "[ num=1 OR ]",
        "OR num=1",
    ]

    def test_good_conditions(self):
        for cond in self.GOOD:
            matcher = matching.ConditionParser(lookup, "name").parse(cond)
            assert isinstance(matcher, matching.Filter), "Matcher is not a filter" 
            assert matcher, "Matcher is empty" 

    def test_bad_conditions(self):
        for cond in self.BAD:
            try:
                matcher = matching.ConditionParser(lookup).parse(cond)
            except matching.FilterError, exc:
                log.info("'%s' ==> %s" % (cond, exc))
            else:
                assert False, "[ %s ] '%s' raised no error" % (matcher, cond)


if __name__ == "__main__":
    unittest.main()
