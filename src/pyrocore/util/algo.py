""" PyroCore - Helper Algorithms.

    Copyright (c) 2009, 2010 The PyroScope Project <pyroscope.project@gmail.com>

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

log = logging.getLogger(__name__)


try:
    from itertools import product #@UnusedImport
except ImportError:
    def product(*args, **kwds):
        """ product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
            product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
        """
        pools = map(tuple, args) * kwds.get('repeat', 1)
        result = [[]]
        for pool in pools:
            result = [x+[y] for x in result for y in pool]
        for prod in result:
            yield tuple(prod)


class AttributeMapping(object):

    def __init__(self, obj, defaults=None):
        """ Remember object we want to map.
        """
        self.obj = obj
        self.defaults = defaults or {}


    def __getitem__(self, key):
        """ Return object attribute named C{key}.
        """
        ##print "GETITEM", key, self.defaults
        try:
            return getattr(self.obj, key)
        except AttributeError:
            return self.defaults[key]
