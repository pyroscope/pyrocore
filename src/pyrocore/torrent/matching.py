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
        self._condition = value
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
        super(GlobFilter, self).validate()
        self._value = self._value.lower()


    def match(self, item):
        """ Return True if filter matches item.
        """
        return fnmatch.fnmatchcase(getattr(item, self._name).lower(), self._value) 


class BoolFilter(FieldFilter):
    """ Filter boolean values.
    """
    TRUE = ["true", "t", "yes", "y", "1", "+",]
    FALSE = ["false", "f", "no", "n", "0", "-",]


    def validate(self):
        """ Validate filter condition (template method).
        """
        super(BoolFilter, self).validate()
        
        lower_val = self._value.lower()
        if lower_val in self.TRUE:
            self._value = True
        elif lower_val in self.FALSE:
            self._value = False
        else:
            raise FilterError("Bad boolean value %r in %r (expected one of '%s', or '%s')" % (
                self._value, self._condition, "' '".join(self.TRUE), "' '".join(self.FALSE)
            ))  


    def match(self, item):
        """ Return True if filter matches item.
        """
        return bool(getattr(item, self._name)) is self._value  


class NumericFilterBase(FieldFilter):
    """ Base class for numerical value filters.
    """

    def validate(self):
        """ Validate filter condition (template method).
        """
        super(NumericFilterBase, self).validate()

        if self._value.startswith('+'):
            self._cmp = lambda a,b: a > b
            self._value = self._value[1:]
        elif self._value.startswith('-'):
            self._cmp = lambda a,b: a < b
            self._value = self._value[1:]
        else:
            self._cmp = lambda a,b: a == b


    def match(self, item):
        """ Return True if filter matches item.
        """
#        if getattr(item, self._name):
#            print "%r %r %r %r %r %r" % (self._cmp(float(getattr(item, self._name)), self._value), 
#                  self._name, self._condition, item.name, getattr(item, self._name), self._value)
        return self._cmp(float(getattr(item, self._name)), self._value) 


class FloatFilter(NumericFilterBase):
    """ Filter float values.
    """

    def validate(self):
        """ Validate filter condition (template method).
        """
        super(FloatFilter, self).validate()

        try:
            self._value = float(self._value)
        except (ValueError, TypeError), exc:
            raise FilterError("Bad numerical value %r in %r (%s)" % (self._value, self._condition, exc))  


class ByteSizeFilter(NumericFilterBase):
    """ Filter size and bandwidth values.
    """
    UNITS = dict(b=1, k=1024, m=1024**2, g=1024**3)

    def validate(self):
        """ Validate filter condition (template method).
        """
        super(ByteSizeFilter, self).validate()

        # Get scale
        lower_val = self._value.lower()
        if any(lower_val.endswith(i) for i in self.UNITS):
            scale = self.UNITS[lower_val[-1]]
            self._value = self._value[:-1]
        else:
            scale = 1

        # Get float value
        try:
            self._value = float(self._value)
        except (ValueError, TypeError), exc:
            raise FilterError("Bad numerical value %r in %r (%s)" % (self._value, self._condition, exc))  

        # Scale to bytes
        self._value = self._value * scale
