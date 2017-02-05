# -*- coding: utf-8 -*-
# pylint: disable=
""" Unit Tests.

    Copyright (c) 2009, 2010 The PyroScope Project <pyroscope.project@gmail.com>
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
import sys
import logging

# Add a level more detailed than DEBUG
TRACE = logging.DEBUG-1


class TestLogger(logging.Logger):
    """A logger with trace()."""

    @classmethod
    def initialize(cls):
        """ Register test logging.
        """
        logging.addLevelName(TRACE, "TRACE")
        logging.setLoggerClass(cls)

        if any(i in sys.argv for i in ("-v", "--verbose")):
            logging.getLogger().setLevel(TRACE)
        elif any(i in sys.argv for i in ("-q", "--quiet")):
            logging.getLogger().setLevel(logging.INFO)


    def trace(self, msg, *args, **kwargs):
        """ Micro logging.
        """
        return self.log(TRACE, msg, *args, **kwargs)


    # FlexGet names
    debugall = trace
    verbose = logging.Logger.info


TestLogger.initialize()
