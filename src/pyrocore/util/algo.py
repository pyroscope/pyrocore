# -*- coding: utf-8 -*-
# pylint: disable=
""" Helper Algorithms.

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
from __future__ import absolute_import

import logging

log = logging.getLogger(__name__)


try:
    from itertools import product # @UnusedImport pylint: disable=E0611
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


def flatten(nested, containers=(list, tuple)):
    """ Flatten a nested list in-place and return it.
    """
    flat = list(nested) # handle iterators / generators
    i = 0
    while i < len(flat):
        while isinstance(flat[i], containers):
            if not flat[i]:
                # kill empty list
                flat.pop(i)

                # inspect new 'i'th element in outer loop
                i -= 1
                break
            else:
                flat[i:i + 1] = (flat[i])

        # 'i'th element is scalar, proceed
        i += 1

    return flat


class AttributeMapping(object):
    """ Wrap an object's dict so that it can be accessed by the mapping protocol.
    """

    def __init__(self, obj, defaults=None):
        """ Store object we want to map, and any default values.

            @param obj: the wrapped object
            @type obj: object
            @param defaults: default values
            @type defaults: dict
        """
        self.obj = obj
        self.defaults = defaults or {}


    def __getitem__(self, key):
        """ Return object attribute named C{key}.
        """
        ##print "GETITEM", key, self.defaults
        try:
            return getattr(self.obj, key)
        except AttributeError as exc:
            try:
                return self.defaults[key]
            except KeyError:
                raise AttributeError("%s for %r.%s" % (exc, self.obj, key))
