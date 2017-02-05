# -*- coding: utf-8 -*-
# pylint: disable=
""" FlexGet Plugin Tests.

    Copyright (c) 2011 The PyroScope Project <pyroscope.project@gmail.com>
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
import imp
import sys
import logging

''' TODO: unbreak this

from pyrocore.util import os
from pyrocore.flexget import FLEXGET_BOOTSTRAP
import tests

log = logging.getLogger(__name__)


def load_flexget_tests():
    """ Try to load FlexGet test support.
    """
    try:
        import flexget
    except ImportError:
        return None
    else:
        flexget_tests_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(flexget.__file__))), "tests")
        #print flexget_tests_dir
        if os.path.isdir(flexget_tests_dir):
            tests.__path__.append(flexget_tests_dir) #@UndefinedVariable
            imp.acquire_lock()
            try:
                fp, path, info = imp.find_module('__init__', [flexget_tests_dir])
                try:
                    flexget_tests = imp.load_module("flexget_tests", fp, path, info)
                    sys.modules["flexget_tests"] = flexget_tests
                finally:
                    if fp:
                        fp.close()
            finally:
                imp.release_lock()

    return flexget_tests


if os.path.exists(os.path.expanduser(FLEXGET_BOOTSTRAP)) and load_flexget_tests():
    from flexget_tests import FlexGetBase #@UnresolvedImport
    from flexget import plugin

    class TestCondition(FlexGetBase):
        __yaml__ = """
            presets:
              global:
                disable_builtins: [seen]
                mock:
                  - {title: 'test', year: 2000}
                  - {title: 'brilliant', rating: 9.9}
                  - {title: 'fresh', year: 2011}

            feeds:
              test_condition_reject:
                pyro_reject_if: year<2011

              test_condition_accept:
                pyro_accept_if:
                  - ?year>=2010
                  - ?rating>9

              test_condition_and1:
                pyro_accept_if: '*t ?rating>9'
              test_condition_and2:
                pyro_accept_if: '*t'
        """

        def test_reject(self):
            self.execute_feed('test_condition_reject')
            count = len(self.feed.rejected)
            assert count == 1

        def test_accept(self):
            self.execute_feed('test_condition_accept')
            count = len(self.feed.accepted)
            assert count == 2

        def test_implicit_and(self):
            for i in "12":
                self.execute_feed('test_condition_and' + i)
                count = len(self.feed.accepted)
                assert count == int(i)


    class TestDownloadCondition(FlexGetBase):
        __yaml__ = """
            presets:
              global:
                disable_builtins: [seen]
                mock:
                  - {title: 'test', file: 'tests/test.torrent'}
                  - {title: 'prv', file: 'tests/private.torrent'}
                  - {title: 'not_a_torrent'}

            feeds:
              test_condition_field_access1:
                pyro_reject_if_download: ?torrent.content.info.?private=1

              test_condition_field_access2:
                pyro_reject_if_download: ?torrent.content.announce=*openbittorrent.com[/:]*
        """

        def test_field_access(self):
            for i in "12":
                self.execute_feed('test_condition_field_access' + i)
                count = len(self.feed.rejected)
                assert count == int(i), "Expected %s rejects, got %d" % (i, count)
                assert i != "1" or self.feed.rejected[0]["title"] == "prv"


    class TestQualityCondition(FlexGetBase):
        __yaml__ = """
            presets:
              global:
                disable_builtins: [seen]
                mock:
                  - {title: 'Smoke.1280x720'}
                  - {title: 'Smoke.720p'}
                  - {title: 'Smoke.1080i'}
                  - {title: 'Smoke.HDTV'}
                  - {title: 'Smoke.cam'}
                  - {title: 'Smoke.HR'}
                accept_all: yes

            feeds:
              test_condition_quality_name_2:
                pyro_reject_if: quality.name~(1080|720)p

              test_condition_quality_value_3:
                pyro_reject_if: quality.value<500
        """

        def test_quality(self):
            for feedname in self.manager.config['feeds']:
                self.execute_feed(feedname)
                count = len(self.feed.rejected)
                expected = int(feedname[-1])
                assert count == expected, "Expected %s rejects, got %d" % (expected, count)


    # TODO: For meaningful tests, pyrocore must get mock support (specifically for xmlrpc)
    class TestRtorrentUnavailable(FlexGetBase):
        """Tests that can run without pyrocore installed."""

        # Note we enforce an error here if pyrocore is installed, so we can test
        # that disabling the plugin causes no unwanted calls (they'd raise).
        __tmp__ = True
        __yaml__ = """
            presets:
              global:
                rtorrent_view:
                  enabled: no
                  config_dir: __tmp__

            feeds:
              test_rtorrent_disabled:
                rtorrent_view:
                  enabled: no
        """

        def test_rtorrent_disabled(self):
            "Test 'enabled' flag"
            self.execute_feed('test_rtorrent_disabled')

            rtorrent = plugin.get_plugin_by_name("rtorrent_view") #@UndefinedVariable
            assert rtorrent.instance.proxy is None
            assert rtorrent.instance.global_config is not None

        #def test_rtorrent_config(self):
        #    "Test different config layouts"
'''
