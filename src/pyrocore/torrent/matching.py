# -*- coding: utf-8 -*-
# pylint: disable-msg=I0011
""" PyroCore - Torrent Item Filters.

    Copyright (c) 2009, 2010 The PyroScope Project <pyrocore.project@gmail.com>

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
import fnmatch

from pyrocore import error


class FilterError(error.UserError):
    """ (Syntax) error in filter.
    """


class Filter(object):
    """ Base class for all filters.
    """

    def match(self, item):
        """ Return True if filter matches item.
        """
        raise NotImplementedError()


class CompoundFilterAll(Filter, list):
    """ List of filters that must all match.
    """

    def match(self, item):
        """ Return True if filter matches item.
        """
        return all(i.match(item) for i in self)


class CompoundFilterAny(Filter, list):
    """ List of filters where at least one must match.
    """

    def match(self, item):
        """ Return True if filter matches item.
        """
        return any(i.match(item) for i in self)


class NegateFilter(object):
    """ Negate result of another filter.
    """

    def __init__(self, inner):
        self._inner = inner


    def match(self, item):
        """ Return True if filter matches item.
        """
        return not self._inner.match(item)


class FieldFilter(Filter):
    """ Base class for all field filters.
    """

    def __init__(self, name, value):
        """ Store field name and filter value for later evaluations. 
        """
        self._name = name
        self._value = value
        self.validate()


    def validate(self):
        """ Validate filter condition (template method).
        """


class GlobFilter(FieldFilter):
    """ Case-insensitive glob pattern filter.
    """

    def validate(self):
        """ Validate filter condition (template method).
        """
        self._value = self._value.lower()


    def match(self, item):
        """ Return True if filter matches item.
        """
        return fnmatch.fnmatchcase(getattr(item, self._name).lower(), self._value) 
