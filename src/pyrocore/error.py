""" PyroCore - Exception Classes.

    Copyright (c) 2010 The PyroScope Project <pyroscope.project@gmail.com>

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

class LoggableError(Exception):
    """ An exception that is intended to be logged instead of passing it to the
        runtime environment which will likely produce a full stacktrace.
    """


class EngineError(LoggableError):
    """ Connection or other backend error.
    """


class UserError(LoggableError):
    """ Yes, it was your fault!
    """

