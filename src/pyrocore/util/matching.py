# -*- coding: utf-8 -*-
# pylint: disable=I0011
""" PyroCore - Torrent Item Filters.

    Copyright (c) 2009, 2010, 2011 The PyroScope Project <pyroscope.project@gmail.com>

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
import re
import time
import fnmatch
import operator

from pyrocore import error


def _time_ym_delta(timestamp, delta, months):
    """ Helper to add a year or month delta to a timestamp.
    """
    timestamp = list(time.localtime(timestamp))
    timestamp[int(months)] += delta
    return time.mktime(timestamp)


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

    def __call__(self, item):
        return self.match(item)


class CompoundFilterBase(Filter, list):
    """ List of filters.
    """


class CompoundFilterAll(CompoundFilterBase):
    """ List of filters that must all match (AND).
    """

    def __str__(self):
        return ' '.join(str(i) for i in self)

    def match(self, item):
        """ Return True if filter matches item.
        """
        return all(i.match(item) for i in self)


class CompoundFilterAny(CompoundFilterBase):
    """ List of filters where at least one must match (OR).
    """

    def __str__(self):
        if all(isinstance(i, FieldFilter) for i in self) and len(set(i._name for i in self)) == 1:
            return "%s,%s" % (str(self[0]), ','.join(i._condition for i in self[1:]))
        else:
            return "[ %s ]" % ' OR '.join(str(i) for i in self)

    def match(self, item):
        """ Return True if filter matches item.
        """
        return any(i.match(item) for i in self)


class NegateFilter(Filter):
    """ Negate result of another filter (NOT).
    """

    def __init__(self, inner):
        self._inner = inner

    def __str__(self):
        if isinstance(self._inner, FieldFilter):
            return "%s=!%s" % tuple(str(self._inner).split('=', 1))
        else:
            return "NOT " + str(self._inner)

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


    def __str__(self):
        return "%s=%s" % (self._name, self._condition)


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


class FilesFilter(GlobFilter):
    """ Case-insensitive glob pattern filter on filenames in a torrent.
    """

    def match(self, item):
        """ Return True if filter matches item.
        """
        for fileinfo in getattr(item, self._name):
            if fnmatch.fnmatchcase(fileinfo.path.lower(), self._value):
                return True
        return False


class TaggedAsFilter(FieldFilter):
    """ Case-insensitive tags filter. Tag fields are white-space separated lists
        of tags.
    """

    def validate(self):
        """ Validate filter condition (template method).
        """
        super(TaggedAsFilter, self).validate()
        self._value = self._value.lower()

        # If the tag starts with '=', test on equality (just this tag, no others)
        if self._value.startswith('='):
            self._exact = True
            self._value = self._value[1:]
        else:
            self._exact = not self._value

        # For exact matches, value is the set to compare to
        if self._exact:
            # Empty tag means empty set, not set of one empty string
            self._value = set((self._value,)) if self._value else set()


    def match(self, item):
        """ Return True if filter matches item.
        """
        tags = getattr(item, self._name)

        if self._exact:
            # Equality check
            return self._value == set(tags)
        else:
            # Is given tag in list?
            return self._value in tags


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
            
        self._condition = "yes" if self._value else "no" 


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
            self._cmp = operator.gt
            self._value = self._value[1:]
        elif self._value.startswith('-'):
            self._cmp = operator.lt
            self._value = self._value[1:]
        else:
            self._cmp = operator.eq


    def match(self, item):
        """ Return True if filter matches item.
        """
        if 0 and getattr(item, self._name):
            print "%r %r %r %r %r %r" % (self._cmp(float(getattr(item, self._name)), self._value), 
                  self._name, self._condition, item.name, getattr(item, self._name), self._value)
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


class TimeFilter(NumericFilterBase):
    """ Filter UNIX timestamp values.
    """

    TIMEDELTA_UNITS = dict(
        y = lambda t, d: _time_ym_delta(t, -d, False),
        m = lambda t, d: _time_ym_delta(t, -d, True),
        w = lambda t, d: t - d * 7 * 86400,
        d = lambda t, d: t - d * 86400,
        h = lambda t, d: t - d * 3600,
        i = lambda t, d: t - d * 60,
        s = lambda t, d: t - d, 
    )
    TIMEDELTA_RE = re.compile("^%s$" % ''.join(
        r"(?:(?P<%s>\d+)[%s%s])?" % (i, i, i.upper()) for i in "ymwdhis"
    ))


    def validate(self, duration=False):
        """ Validate filter condition (template method).
        """
        super(TimeFilter, self).validate()
        timestamp = now = time.time()

        if self._value.isdigit():
            # Literal UNIX timestamp
            try:
                timestamp = float(self._value)
            except (ValueError, TypeError), exc:
                raise FilterError("Bad timestamp value %r in %r (%s)" % (self._value, self._condition, exc))  
        else:
            # Something human readable
            delta = self.TIMEDELTA_RE.match(self._value)
            ##print self.TIMEDELTA_RE.pattern
            if delta:
                # Time delta
                for unit, val in delta.groupdict().items():
                    if val:
                        timestamp = self.TIMEDELTA_UNITS[unit](timestamp, int(val, 10))  

                if duration:
                    timestamp = now - timestamp
                else:
                    # Invert logic for time deltas (+ = older; - = within the delta range)
                    if self._cmp == operator.lt:
                        self._cmp = operator.gt
                    elif self._cmp == operator.gt:
                        self._cmp = operator.lt
            else:
                # Assume it's an absolute date
                if '/' in self._value:
                    # U.S.
                    fmt = "%m/%d/%Y"
                elif '.' in self._value:
                    # European
                    fmt = "%d.%m.%Y"
                else:
                    # Fall back to ISO
                    fmt = "%Y-%m-%d"

                val = self._value.upper().replace(' ', 'T')
                if 'T' in val:
                    # Time also given
                    fmt += "T%H:%M:%S"[:3+3*val.count(':')]

                try:
                    timestamp = time.mktime(time.strptime(val, fmt))
                except (ValueError), exc:
                    raise FilterError("Bad timestamp value %r in %r (%s)" % (self._value, self._condition, exc))

                if duration:
                    timestamp -= now

        self._value = timestamp
        ##print time.time() - self._value
        ##print time.localtime(time.time())
        ##print time.localtime(self._value)
            

class DurationFilter(TimeFilter):
    """ Filter durations in seconds.
    """

    def validate(self):
        """ Validate filter condition (template method).
        """
        super(DurationFilter, self).validate(duration=True)


    def match(self, item):
        """ Return True if filter matches item.
        """
        if getattr(item, self._name) is None:
            # Never match "N/A" items, except when "-0" was specified
            return False if self._value else self._cmp(-1, 0) 
        else:
            return super(DurationFilter, self).match(item)


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


class ConditionParser(object):
    """ Filter condition parser.
    """

    def __init__(self, lookup):
        """ Initialize parser.
        
            The C{lookup} callback takes a C{name} argument and returns a dict describing
            that field, or None for an unknown field. If a dict is returned, the "matcher"
            key is supposed to be a C{Filter} instance; if it's None or missing, the field
            is not comparable.
        
            @param lookup: Field lookup callable. 
        """
        self.lookup = lookup

    
    def _create_filter(self, condition):
        """ Create a filter object from a textual condition.
        """
        # Split name from value(s)
        try:
            name, values = condition.split('=', 1)
        except ValueError:
            name, values = "name", condition
    
        # Try to find field definition
        field = self.lookup(name)
        if not field:
            raise FilterError("Unknown field %r in %r" % (name, condition))  
        if field.get("matcher") is None: 
            raise FilterError("Field %r cannot be used as a filter" % (name,))  
    
        # Make filters from values
        filters = []
        for value in values.split(','):
            wrapper = None
            if value.startswith('!'):
                wrapper = NegateFilter
                value = value[1:]
            field_matcher = field["matcher"](name, value)
            filters.append(wrapper(field_matcher) if wrapper else field_matcher)
    
        # Return filters
        return CompoundFilterAny(filters) if len(filters) > 1 else filters[0]  
    
    
    def _tree2str(self, tree, root=True):
        """ Convert parsed condition tree back to a (printable) string.
        """
        try:
            # Keep strings as they are
            return '' + tree
        except (TypeError, ValueError):
            flat = ' '.join(self._tree2str(i, root=False) for i in tree)
            return flat if root else "[ %s ]" % flat
        
    
    def parse(self, conditions):
        """ Parse filter conditions.
        
            @param conditions: multiple conditions.
            @type conditions: list or str 
        """
        conditions_text = conditions
        try:
            conditions = conditions.split()
        except AttributeError:
            # Not a string, assume parsed tree
            conditions_text = self._tree2str(conditions)
    
        # Empty list?
        if not conditions:
            raise FilterError("No conditions given at all!")
    
        # Handle grouping
        if '[' in conditions:
            tree = [[]]
            for term in conditions:
                if term == '[':
                    tree.append([]) # new grouping
                elif term == ']':
                    subtree = tree.pop()
                    if not tree:
                        raise FilterError("Unbalanced brackets, too many closing ']' in condition %r" % (conditions_text,))
                    tree[-1].append(subtree) # append finished group to containing level
                else:
                    tree[-1].append(term) # append to current level
    
            if len(tree) > 1:
                raise FilterError("Unbalanced brackets, too many open '[' in condition %r" % (conditions_text,))
            conditions = tree[0]
    
        # Prepare root matcher
        conditions = list(conditions)
        matcher = CompoundFilterAll()
        if "OR" in conditions:
            root = CompoundFilterAny()
            root.append(matcher)
        else:
            root = matcher
    
        # Go through conditions and parse them
        for condition in conditions:
            if condition == "OR":
                # Leading OR, or OR OR in sequence?
                if not matcher:
                    raise FilterError("Left-hand side of OR missing in %r!" % (conditions_text,))
    
                # Start next run of AND conditions
                matcher = CompoundFilterAll()
                root.append(matcher)
            elif isinstance(condition, list):
                matcher.append(self.parse(condition))
            else:
                matcher.append(self._create_filter(condition))
    
        # Trailing OR?
        if not matcher:
            raise FilterError("Right-hand side of OR missing in %r!" % (conditions_text,))
    
        return root
