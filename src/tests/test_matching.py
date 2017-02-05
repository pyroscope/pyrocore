# -*- coding: utf-8 -*-
# pylint: disable=
""" Filter condition tests.

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
import time
import logging
import unittest

from pyrobase.parts import Bunch
from pyrocore.util import matching

log = logging.getLogger(__name__)
log.trace("module loaded")


def lookup(name):
    """ Lookup for test fields.
    """
    matchers = dict(
        name = matching.PatternFilter,
        num = matching.FloatFilter,
        flag = matching.BoolFilter,
        tags = matching.TaggedAsFilter,
    )
    return {"matcher": matchers[name]} if name in matchers else None


class FilterTest(unittest.TestCase):
    DATA = [
        Bunch(name="T1", num=1, flag=True, tags=set("ab")),
        Bunch(name="F0", num=0, flag=False, tags=set()),
        Bunch(name="T11", num=11, flag=True, tags=set("b")),
    ]
    CASES = [
        ("flag=y", "T1 T11"),
        ("num=-1", "F0"),
        ("num=-2", "F0 T1"),
        ("num=+99", ""),
        ("num>10", "T11"),
        ("num>11", ""),
        ("num>=11", "T11"),
        ("num<=11", "F0 T1 T11"),
        ("num<11", "F0 T1"),
        ("num<>1", "F0 T11"),
        ("num!=1", "F0 T11"),
        ("T?", "T1"),
        ("T*", "T1 T11"),
        ("tags=a", "T1"),
        ("tags=b", "T1 T11"),
        ("tags=a,b", "T1 T11"),
        ("tags==b", "T11"),
        ("tags=", "F0"),
        ("tags=!", "T1 T11"),
        ("tags=!a", "F0 T11"),
    ]

    def test_conditions(self):
        for cond, expected in self.CASES:
            keep = matching.ConditionParser(lookup, "name").parse(cond)
            result = set(i.name for i in self.DATA if keep(i))
            expected = set(expected.split())
            assert result == expected, "Expected %r, but got %r, for '%s' [ %s ]" % (expected, result, cond, keep)


class MagicTest(unittest.TestCase):
    CASES = [
        ("a*", matching.PatternFilter),
        ("y", matching.BoolFilter),
        ("1", matching.FloatFilter),
        ("+1", matching.FloatFilter),
        ("-1", matching.FloatFilter),
        ("1.0", matching.FloatFilter),
        ("1g", matching.ByteSizeFilter),
        ("+4g", matching.ByteSizeFilter),
        ("0b", matching.ByteSizeFilter),
        ("0k", matching.ByteSizeFilter),
        ("0m", matching.ByteSizeFilter),
        ("1m0s", matching.TimeFilter),
        ("2w", matching.TimeFilter),
        ("2w1y", matching.PatternFilter),
    ]

    def check(self, obj, expected, cond):
        assert type(obj) is expected, "%s is not %s for '%s'" % (type(obj).__name__, expected.__name__, cond)

    def test_magic(self):
        for cond, expected in self.CASES:
            matcher = matching.ConditionParser(lambda _: {"matcher": matching.MagicFilter}, "f").parse(cond)
            log.debug("MAGIC: '%s' ==> %s" % (cond, type(matcher[0]._inner).__name__))
            self.check(matcher[0]._inner, expected, cond)

    def test_magic_negate(self):
        matcher = matching.ConditionParser(lambda _: {"matcher": matching.MagicFilter}, "f").parse("!")
        self.check(matcher[0], matching.NegateFilter, "!")
        self.check(matcher[0]._inner, matching.MagicFilter, "!")
        self.check(matcher[0]._inner._inner, matching.PatternFilter, "!")

    def test_magic_matching(self):
        item = Bunch(name="foo", date=time.time() - 86401, one=1, year=2011, size=1024**2)
        match = lambda c: matching.ConditionParser(
            lambda _: {"matcher": matching.MagicFilter}, "name").parse(c).match(item)

        assert match("f??")
        assert match("name=f*")
        assert match("date=+1d")
        assert match("one=y")
        assert match("one=+0")
        assert match("year=+2000")
        assert match("size=1m")
        assert match("size=1024k")
        assert not match("a*")
        assert not match("date=-1d")
        assert not match("one=false")
        assert not match("one=+1")
        assert not match("year=+2525")
        assert not match("size=-1m")


class ParserTest(unittest.TestCase):
    GOOD = [
        ("num=+1", "%s"),
        ("num>1", "num=+1"),
        ("num<=1", "num=!+1"),
        ("num<1", "num=-1"),
        ("num>=1", "num=!-1"),
        ("num!=1", "num=!1"),
        ("num<>1", "num=!1"),
        ("flag=y", "%ses"),
        ("some*name", "name=%s"),
        ("foo bar", "name=foo name=bar"),
        ("foo,bar", "name=%s"),
        ("foo OR bar", "[ name=foo OR name=bar ]"),
    ]
    BAD = [
        "",
        "num=foo",
        "num>-1",
        "num>+1",
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
        for cond, canonical in self.GOOD:
            if '%' in canonical:
                canonical = canonical % cond
            matcher = matching.ConditionParser(lookup, "name").parse(cond)
            assert isinstance(matcher, matching.Filter), "Matcher is not a filter"
            assert str(matcher) == canonical, "'%s' != '%s'" % (matcher, canonical)
            assert matcher, "Matcher is empty"

    def test_bad_conditions(self):
        for cond in self.BAD:
            try:
                matcher = matching.ConditionParser(lookup).parse(cond)
            except matching.FilterError, exc:
                log.debug("BAD: '%s' ==> %s" % (cond, exc))
            else:
                assert False, "[ %s ] '%s' raised no error" % (matcher, cond)


if __name__ == "__main__":
    unittest.main()
