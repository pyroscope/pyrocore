# -*- coding: utf-8 -*-
# pylint: disable=bad-whitespace
""" Exception Classes.

    Copyright (c) 2010 The PyroScope Project <pyroscope.project@gmail.com>
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

# Return codes according to /usr/include/sysexits.h
EX_OK           =  0 # successful termination
EX__BASE        = 64 # base value for error messages
EX_USAGE        = 64 # command line usage error
EX_DATAERR      = 65 # data format error
EX_NOINPUT      = 66 # cannot open input
EX_NOUSER       = 67 # addressee unknown
EX_NOHOST       = 68 # host name unknown
EX_UNAVAILABLE  = 69 # service unavailable
EX_SOFTWARE     = 70 # internal software error
EX_OSERR        = 71 # system error (e.g., can't fork)
EX_OSFILE       = 72 # critical OS file missing
EX_CANTCREAT    = 73 # can't create (user) output file
EX_IOERR        = 74 # input/output error
EX_TEMPFAIL     = 75 # temp failure; user is invited to retry
EX_PROTOCOL     = 76 # remote error in protocol
EX_NOPERM       = 77 # permission denied
EX_CONFIG       = 78 # configuration error
EX__MAX         = 78 # maximum listed value


class LoggableError(Exception):
    """ An exception that is intended to be logged instead of passing it to the
        runtime environment which will likely produce a full stacktrace.
    """


class EngineError(LoggableError):
    """ Connection or other backend error.
    """


class NetworkError(LoggableError):
    """ External connection errors.
    """


class UserError(LoggableError):
    """ Yes, it was your fault!
    """
