# -*- coding: utf-8 -*-
# pylint: disable=
""" Torrent Item Filters.

    Copyright (c) 2009, 2010, 2011 The PyroScope Project <pyroscope.project@gmail.com>
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
import re
import time
import shlex
import fnmatch
import operator

from pyrocore import error, config
from pyrocore.util import fmt, pymagic

log = pymagic.get_lazy_logger(__name__)

TRUE = set(("true", "t", "yes", "y", "1", "+",))
FALSE = set(("false", "f", "no", "n", "0", "-",))


def truth(val, context):
    """ Convert truth value in "val" to a boolean.
    """
    try:
        0 + val
    except TypeError:
        lower_val = val.lower()

        if lower_val in TRUE:
            return True
        elif lower_val in FALSE:
            return False
        else:
            raise FilterError("Bad boolean value %r in %r (expected one of '%s', or '%s')" % (
                val, context, "' '".join(TRUE), "' '".join(FALSE)
            ))
    else:
        return bool(val)


def _time_ym_delta(timestamp, delta, months):
    """ Helper to add a year or month delta to a timestamp.
    """
    timestamp = list(time.localtime(timestamp))
    timestamp[int(months)] += delta
    return time.mktime(timestamp)


def unquote_pre_filter(pre_filter, _regex=re.compile(r'[\\]+')):
    """ Unquote a pre-filter condition.
    """
    if pre_filter.startswith('"') and pre_filter.endswith('"'):
        # Unquote outer level
        pre_filter = pre_filter[1:-1]
        pre_filter = _regex.sub(lambda x: x.group(0)[:len(x.group(0)) // 2], pre_filter)

    return pre_filter


class FilterError(error.UserError):
    """ (Syntax) error in filter.
    """


class Filter(object):
    """ Base class for all filters.
    """

    def pre_filter(self):  # pylint: disable=no-self-use
        """ Return rTorrent condition to speed up data transfer.
        """
        return ''

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

    def pre_filter(self):
        """ Return rTorrent condition to speed up data transfer.
        """
        if len(self) == 1:
            return self[0].pre_filter()
        else:
            result = [x.pre_filter() for x in self if not isinstance(x, CompoundFilterBase)]
            result = [x for x in result if x]
            if result:
                if int(config.fast_query) == 1:
                    return result[0]  # using just one simple expression is safer
                else:
                    # TODO: make this purely value-based (is.nz=…)
                    return 'and={%s}' % ','.join(result)
        return ''

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

    def pre_filter(self):
        """ Return rTorrent condition to speed up data transfer.
        """
        if len(self) == 1:
            return self[0].pre_filter()
        # TODO: Find a safe way to do 'or' expressions
        return ''

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
        elif isinstance(self._inner, CompoundFilterBase):
            return "[ NOT [ %s ] ]" % str(self._inner)
        else:
            return "[ NOT %s ]" % str(self._inner)

    def pre_filter(self):
        """ Return rTorrent condition to speed up data transfer.
        """
        inner = self._inner.pre_filter()
        if inner:
            if inner.startswith('"not=$') and inner.endswith('"') and '\\' not in inner:
                return inner[6:-1]  # double negation, return inner command
            elif inner.startswith('"'):
                inner = '"$' + inner[1:]
            else:
                inner = '$' + inner
            return 'not=' + inner
        else:
            return ''

    def match(self, item):
        """ Return True if filter matches item.
        """
        return not self._inner.match(item)


class FieldFilter(Filter):
    """ Base class for all field filters.
    """

    PRE_FILTER_FIELDS = dict(
        # alias="",
        hash="d.hash=",
        name="d.name=",
        message="d.message=",
        metafile="d.tied_to_file=",
        path="d.base_path=",
        # realpath="=",
        throttle="d.throttle_name=",
        # tracker="=",

        is_active="d.is_active=",
        is_complete="d.complete=",
        is_ignored="d.ignore_commands=",
        is_multi_file="d.is_multi_file=",
        is_open="d.is_open=",

        # done="=",
        down="d.down.rate=",
        # fno="=",
        prio="d.priority=",
        ratio="d.ratio=",
        size="d.size_bytes=",
        up="d.up.rate=",
        uploaded="d.up.total=",

        completed="d.custom=tm_completed",
        loaded="d.custom=tm_loaded",
        started="d.custom=tm_started",
        # stopped="",
        custom_tm_completed="d.custom=tm_completed",
        custom_tm_loaded="d.custom=tm_loaded",
        custom_tm_started="d.custom=tm_started",

        # XXX: bad result: rtcontrol -Q2 -o- -v tagged='!'new,foo
        #       use a 'd.is_tagged=tag' command?
        tagged="d.custom=tags",
    )

        #active                last time a peer was connected
        #directory             directory containing download data
        #files                 list of files in this item
        #is_ghost              has no data file or directory?
        #is_private            private flag set (no DHT/PEX)?
        #leechtime             time taken from start to completion
        #seedtime              total seeding time after completion
        #traits                automatic classification of this item (audio, video, tv, movie, etc.)
        #views                 views this item is attached to
        #xfer                  transfer rate

    def __init__(self, name, value):
        """ Store field name and filter value for later evaluations.
        """
        self._name = name
        self._condition = self._value = fmt.to_unicode(value)
        self.validate()

    def __str__(self):
        return fmt.to_utf8("%s=%s" % (self._name, self._condition))

    def validate(self):
        """ Validate filter condition (template method).
        """


class EqualsFilter(FieldFilter):
    """ Filter fields equal to the given value.
    """

    def match(self, item):
        """ Return True if filter matches item.
        """
        result = self._value == getattr(item, self._name)
        #log.debug("%r for %r = %r, name %r, item %r" % (
        #    result, getattr(item, self._name), self._value, self._name, item))
        return result


class PatternFilter(FieldFilter):
    """ Case-insensitive pattern filter, either a glob or a /regex/ pattern.
    """

    CLEAN_PRE_VAL_RE = re.compile(r'(?:\[.*?]\])|(?:\(.*?]\))|(?:{.*?]})|(?:\\)')
    SPLIT_PRE_VAL_RE = re.compile(r'[^a-zA-Z0-9/_]+')
    SPLIT_PRE_GLOB_RE = re.compile(r'[?*]+')

    def validate(self):
        """ Validate filter condition (template method).
        """
        super(PatternFilter, self).validate()
        self._value = self._value.lower()
        self._is_regex = self._value.startswith('/') and self._value.endswith('/')
        if self._is_regex:
            self._matcher = re.compile(self._value[1:-1]).search
        else:
            self._matcher = lambda val: fnmatch.fnmatchcase(val, self._value)

    def pre_filter(self):
        """ Return rTorrent condition to speed up data transfer.
        """
        if self._name not in self.PRE_FILTER_FIELDS:
            return ''
        if not self._value:
            return '"equal={},cat="'.format(self.PRE_FILTER_FIELDS[self._name])

        if self._is_regex:
            needle = self._value[1:-1]
            needle = self.CLEAN_PRE_VAL_RE.sub(' ', needle)
            needle = self.SPLIT_PRE_VAL_RE.split(needle)
        else:
            needle = self.CLEAN_PRE_VAL_RE.sub(' ', self._value)
            needle = self.SPLIT_PRE_GLOB_RE.split(needle)
        needle = list(sorted(needle, key=len))[-1]

        if needle:
            try:
                needle.encode('ascii')
            except UnicodeEncodeError:
                return ''
            else:
                return '"string.contains_i=${},{}"'.format(
                       self.PRE_FILTER_FIELDS[self._name], needle)

        return ''

    def match(self, item):
        """ Return True if filter matches item.
        """
        val = (getattr(item, self._name) or '').lower()
        #log.debug("%r for %r ~ %r, name %r, item %r" % (
        #    self._matcher(val), val, self._value, self._name, item))
        return self._matcher(val)


class FilesFilter(PatternFilter):
    """ Case-insensitive pattern filter on filenames in a torrent.
    """

    def match(self, item):
        """ Return True if filter matches item.
        """
        val = getattr(item, self._name)
        if val is not None:
            for fileinfo in val:
                if fnmatch.fnmatchcase(fileinfo.path.lower(), self._value):
                    return True
            return False


class TaggedAsFilter(FieldFilter):
    """ Case-insensitive tags filter. Tag fields are white-space separated lists
        of tags.
    """

    def pre_filter(self):
        """ Return rTorrent condition to speed up data transfer.
        """
        if self._name in self.PRE_FILTER_FIELDS:
            if not self._value:
                return '"not=${}"'.format(self.PRE_FILTER_FIELDS[self._name])
            else:
                val = self._value
                if self._exact:
                    val = val.copy().pop()
                return '"string.contains_i=${},{}"'.format(
                       self.PRE_FILTER_FIELDS[self._name], val)
        return ''

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
        tags = getattr(item, self._name) or []
        if self._exact:
            # Equality check
            return self._value == set(tags)
        else:
            # Is given tag in list?
            return self._value in tags


class BoolFilter(FieldFilter):
    """ Filter boolean values.
    """

    def pre_filter(self):
        """ Return rTorrent condition to speed up data transfer.
        """
        if self._name in self.PRE_FILTER_FIELDS:
            return '"equal={},value={}"'.format(
                   self.PRE_FILTER_FIELDS[self._name], int(self._value))
        return ''

    def validate(self):
        """ Validate filter condition (template method).
        """
        super(BoolFilter, self).validate()

        self._value = truth(str(self._value), self._condition)
        self._condition = "yes" if self._value else "no"


    def match(self, item):
        """ Return True if filter matches item.
        """
        val = getattr(item, self._name) or False
        return bool(val) is self._value


class NumericFilterBase(FieldFilter):
    """ Base class for numerical value filters.
    """

    def validate(self):
        """ Validate filter condition (template method).
        """
        super(NumericFilterBase, self).validate()

        self.not_null = False

        if self._value.startswith('+'):
            self._cmp = operator.gt
            self._rt_cmp = 'greater'
            self._value = self._value[1:]
        elif self._value.startswith('-'):
            self._cmp = operator.lt
            self._rt_cmp = 'less'
            self._value = self._value[1:]
        else:
            self._cmp = operator.eq
            self._rt_cmp = 'equal'


    def match(self, item):
        """ Return True if filter matches item.
        """
        if 0 and getattr(item, self._name):
            print "%r %r %r %r %r %r" % (self._cmp(float(getattr(item, self._name)), self._value),
                  self._name, self._condition, item.name, getattr(item, self._name), self._value)
        val = getattr(item, self._name) or 0
        if self.not_null and self._value and not val:
            return False
        else:
            return self._cmp(float(val), self._value)


class FloatFilter(NumericFilterBase):
    """ Filter float values.
    """

    FIELD_SCALE = dict(
        ratio=1000,
    )

    def pre_filter(self):
        """ Return rTorrent condition to speed up data transfer.
        """
        if self._name in self.PRE_FILTER_FIELDS:
            val = int(self._value * self.FIELD_SCALE.get(self._name, 1))
            return '"{}=value=${},value={}"'.format(
                   self._rt_cmp, self.PRE_FILTER_FIELDS[self._name], val)
        return ''

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
        y=lambda t, d: _time_ym_delta(t, -d, False),
        m=lambda t, d: _time_ym_delta(t, -d, True),
        w=lambda t, d: t - d * 7 * 86400,
        d=lambda t, d: t - d * 86400,
        h=lambda t, d: t - d * 3600,
        i=lambda t, d: t - d * 60,
        s=lambda t, d: t - d,
    )
    TIMEDELTA_RE = re.compile("^%s$" % ''.join(
        r"(?:(?P<%s>\d+)[%s%s])?" % (i, i, i.upper()) for i in "ymwdhis"
    ))

    def pre_filter(self):
        """ Return rTorrent condition to speed up data transfer.
        """
        if self._name in self.PRE_FILTER_FIELDS:
            # Adding a day of fuzz to avoid any possible timezone problems
            timestamp = self._value + (
                -86400 if self._rt_cmp == 'greater' else
                86400 if self._rt_cmp == 'less' else 0)
            return '"{}=value=${},value={}"'.format(
                   self._rt_cmp, self.PRE_FILTER_FIELDS[self._name], int(timestamp))
        return ''

    def validate_time(self, duration=False):
        """ Validate filter condition (template method) for timestamps and durations.
        """
        super(TimeFilter, self).validate()
        timestamp = now = time.time()

        if str(self._value).isdigit():
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
                        self._rt_cmp = 'greater'
                    elif self._cmp == operator.gt:
                        self._cmp = operator.lt
                        self._rt_cmp = 'less'
            else:
                # Assume it's an absolute date
                if '/' in self._value:
                    # U.S.
                    dtfmt = "%m/%d/%Y"
                elif '.' in self._value:
                    # European
                    dtfmt = "%d.%m.%Y"
                else:
                    # Fall back to ISO
                    dtfmt = "%Y-%m-%d"

                val = str(self._value).upper().replace(' ', 'T')
                if 'T' in val:
                    # Time also given
                    dtfmt += "T%H:%M:%S"[:3+3*val.count(':')]

                try:
                    timestamp = time.mktime(time.strptime(val, dtfmt))
                except (ValueError), exc:
                    raise FilterError("Bad timestamp value %r in %r (%s)" % (self._value, self._condition, exc))

                if duration:
                    timestamp -= now

        self._value = timestamp
        ##print time.time() - self._value
        ##print time.localtime(time.time())
        ##print time.localtime(self._value)

    def validate(self):
        """ Validate filter condition (template method).
        """
        self.validate_time(duration=False)


class TimeFilterNotNull(TimeFilter):
    """ Filter UNIX timestamp values, ignore unset values unless compared to 0.
    """

    def validate(self):
        """ Validate filter condition (template method).
        """
        super(TimeFilterNotNull, self).validate()
        self.not_null = True


class DurationFilter(TimeFilter):
    """ Filter durations in seconds.
    """

    def validate(self):
        """ Validate filter condition (template method).
        """
        super(DurationFilter, self).validate_time(duration=True)


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

    def pre_filter(self):
        """ Return rTorrent condition to speed up data transfer.
        """
        if self._name in self.PRE_FILTER_FIELDS:
            return '"{}={},value={}"'.format(
                   self._rt_cmp, self.PRE_FILTER_FIELDS[self._name], int(self._value))
        return ''

    def validate(self):
        """ Validate filter condition (template method).
        """
        super(ByteSizeFilter, self).validate()

        # Get scale
        lower_val = str(self._value).lower()
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


class MagicFilter(FieldFilter):
    """ Filter that looks at the comparison value and automatically decides
        what type of filter to use.
    """

    def validate(self):
        """ Validate filter condition (template method).
        """
        val = self._condition.lower()
        if val and val[0] in "+-":
            val = val[1:]

        matcher = PatternFilter
        if not val or val.startswith('/') and val.endswith('/'):
            pass
        elif val.replace('.', '0').isdigit():
            matcher = FloatFilter
        elif self._condition in (TRUE | FALSE):
            matcher = BoolFilter
        elif any(val.endswith(i) for i in ByteSizeFilter.UNITS) and val[:-1].isdigit():
            matcher = ByteSizeFilter
        elif TimeFilter.TIMEDELTA_RE.match(val):
            matcher = TimeFilter

        self._inner = matcher(self._name, self._condition)


    def match(self, item):
        """ Return True if filter matches item.
        """
        return self._inner.match(item)


class ConditionParser(object):
    """ Filter condition parser.
    """
    COMPARISON_OPS = {
        "<":  "-%s",
        "<=": "!+%s",
        ">":  "+%s",
        ">=": "!-%s",
        "<>": "!%s",
        "!=": "!%s",
        "~": "/%s/",
    }


    @classmethod
    def AMENABLE(cls, _):
        """ Prefined lookup mode for typeless access to any field name.
        """
        return {"matcher": MagicFilter}


    def __init__(self, lookup, default_field=None, ident_re=r"[_A-Za-z][_A-Za-z0-9]*"):
        """ Initialize parser.

            The C{lookup} callback takes a C{name} argument and returns a dict describing
            that field, or None for an unknown field. If a dict is returned, the "matcher"
            key is supposed to be a C{Filter} instance; if it's None or missing, the field
            is not comparable.

            @param lookup: Field definition lookup callable.
            @param default_field: Optional default field name for conditions without an operator.
            @param ident_re: Regex describing valid field names.
        """
        self.lookup = lookup
        self.default_field = default_field
        self.ident_re = ident_re


    def _create_filter(self, condition):
        """ Create a filter object from a textual condition.
        """
        # "Normal" comparison operators?
        comparison = re.match(r"^(%s)(<[>=]?|>=?|!=|~)(.*)$" % self.ident_re, condition)
        if comparison:
            name, comparison, values = comparison.groups()
            if values and values[0] in "+-":
                raise FilterError("Comparison operator cannot be followed by '%s' in '%s'" % (values[0], condition))
            values = self.COMPARISON_OPS[comparison] % values
        else:
            # Split name from value(s)
            try:
                name, values = condition.split('=', 1)
            except ValueError:
                if self.default_field:
                    name, values = self.default_field, condition
                else:
                    raise FilterError("Field name missing in '%s' (expected '=')" % condition)

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
            conditions = shlex.split(fmt.to_utf8(conditions))
        except AttributeError:
            # Not a string, assume parsed tree
            conditions_text = self._tree2str(conditions)

        # Empty list?
        if not conditions:
            raise FilterError("No conditions given at all!")

        # NOT *must* appear at the start of a group
        negate = conditions[:1] == ["NOT"]
        if negate:
            conditions = conditions[1:]
            if not conditions:
                raise FilterError("NOT must be followed by some conditions!")

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

        return NegateFilter(root) if negate else root
