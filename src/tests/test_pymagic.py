# -*- coding: utf-8 -*-
# pylint: disable=
""" Python utilities tests.

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

from pyrocore.util import pymagic

log = logging.getLogger(__name__)
log.trace("module loaded")


class ImportTest(unittest.TestCase):

    def test_import_name(self):
        docstr = pymagic.import_name("pyrocore", "__doc__")
        assert "Core Package" in docstr

        docstr = pymagic.import_name("pyrocore.util", "__doc__")
        assert "Utility Modules" in docstr


    def test_import_fail(self):
        try:
            pymagic.import_name("pyrocore.does_not_exit", "__doc__")
        except ImportError, exc:
            assert "pyrocore.does_not_exit" in str(exc), str(exc)
        else:
            assert False, "Import MUST fail!"


    def test_import_colon(self):
        docstr = pymagic.import_name("pyrocore:__doc__")
        assert "Core Package" in docstr


    def test_import_missing_colon(self):
        try:
            pymagic.import_name("pyrocore")
        except ValueError, exc:
            assert "pyrocore" in str(exc), str(exc)
        else:
            assert False, "Import MUST fail!"


class LogTest(unittest.TestCase):

    def test_get_class_logger(self):
        logger = pymagic.get_class_logger(self)
        assert logger.name == "tests.test_pymagic.LogTest"


if __name__ == "__main__":
    unittest.main()
