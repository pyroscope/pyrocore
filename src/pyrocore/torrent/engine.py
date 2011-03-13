# -*- coding: utf-8 -*-
# pylint: disable=I0011,R0903
""" PyroCore - Torrent Engine Interface.

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
import operator

from pyrocore import config, error 
from pyrocore.util import os, pymagic, fmt, traits, algo
from pyrocore.torrent import matching 


#
# Conversion Helpers
#
def untyped(val):
    """ A type specifier for fields that does nothing.
    """
    return val


def ratio_float(intval):
    """ Convert scaled integer ratio to a normalized float.
    """
    return intval / 1000.0


def percent(floatval):
    """ Convert float ratio to a percent value.
    """
    return floatval * 100.0


def _duration(start, end):
    """ Return time delta.
    """
    if start and end:
        if start > end:
            return None
        else:
            return end - start
    elif start:
        return time.time() - start
    else:
        return None


def _interval_sum(interval, start=None, end=None, context=None, event_re=re.compile("[A-Z][0-9]+")):
    """ Return sum of intervals between "R"esume and "P"aused events
        in C{interval}, optionally limited by a time window defined 
        by C{start} and C{end}. Return None if there's no sensible
        information.
    
        C{interval} is a series of event types and timestamps, 
        e.g. "R1283008245P1283008268".
    """
    def split_event(event):
        "Helper to parse events."
        kind, val = event[:1], event[1:]
        try:
            return kind, float(val)
        except (TypeError, ValueError):
            return None, 0

    end = end and float(end) or time.time()
    events = list(reversed(event_re.findall(interval)))
    result = []

    while events:
        event, resumed = split_event(events.pop())
        ##print "~~~~~~~~~~", context, event, resumed

        if event != "R":
            # Ignore other events
            continue
        resumed = max(resumed, start or resumed)

        if events: # Further events?
            if not events[-1].startswith("P"):
                continue # If not followed by "P", it's not a valid interval
            _, paused = split_event(events.pop())
            paused = min(paused, end)
        else:
            # Currently active, ends at time window
            paused = end

        ##print "~~~~~~~~~~ R: %r, P: %r" % (resumed, paused)
        ##print "~~~~~~~~~~ I: %r" % (paused - resumed)
        if resumed >= paused:
            # Ignore empty intervals
            continue

        result.append(paused - resumed)

    return sum(result) if result else None


def _fmt_duration(duration):
    """ Format duration value.
    """
    return fmt.human_duration(duration, 0, 2, True)


def _fmt_tags(tagset):
    """ Convert set of strings to sorted space-separated list as a string.
    """
    return ' '.join(sorted(tagset))


def _fmt_files(filelist):
    """ Produce a file listing.
    """
    depth = max(i.path.count('/') for i in filelist)
    pad = [u'\uFFFE'] * depth

    base_indent = ' ' * 38
    indent = 0
    result = []
    prev_path = pad
    sorted_files = sorted((i.path.split('/')[:-1]+pad, i.path.rsplit('/', 1)[-1], i) for i in filelist)

    for path, name, fileinfo in sorted_files:
        path = path[:depth]
        if path != prev_path:
            common = min([depth] + [idx
                for idx, (dirname, prev_name) in enumerate(zip(path, prev_path))
                if dirname != prev_name
            ])
            #result.append("!!%r %r" % (indent, common))
            #result.append("!!%r" % (prev_path,))
            #result.append("!!%r" % (path,))

            while indent > common:
                indent -= 1
                result.append("%s%s/" % (base_indent, ' ' * indent))
            
            for dirname in path[common:]:
                if dirname == u'\uFFFE':
                    break
                result.append("%s%s\\ %s" % (base_indent, ' ' * indent, dirname))
                indent += 1
        
        ##result.append("!!%r %r" % (path, name))
        result.append("  %s %s %s %s| %s" % (
            {0: "off ", 1: "    ", 2: "high"}.get(fileinfo.prio, "????"),
            fmt.iso_datetime(fileinfo.mtime),
            fmt.human_size(fileinfo.size),
            ' ' * indent, name,
        ))

        prev_path = path

    while indent > 0:
        indent -= 1
        result.append("%s%s/" % (base_indent, ' ' * indent))
    result.append("%s= %d file(s)" % (base_indent, len(filelist)))

    return '\n'.join(result)


def detect_traits(item):
    """ Build traits list from attributes of the passed item. Currently,
        "kind_51", "name" and "alias" are considered.
    
        See pyrocore.util.traits:dectect_traits for more details.
    """
    return traits.detect_traits(
        name=item.name, alias=item.alias,
        filetype=(list(item.fetch("kind_51")) or [None]).pop(),
    )


#
# Field Descriptors
#
class FieldDefinition(object):
    """ Download item field.
    """
    FIELDS = {}

    def __init__(self, valtype, name, doc, accessor=None, matcher=None, formatter=None, engine_name=None):
        self.valtype = valtype
        self.name = name
        self.__doc__ = doc
        self._engine_name = engine_name
        self._accessor = accessor
        self._matcher = matcher
        self._formatter = formatter

        if name in FieldDefinition.FIELDS:
            raise RuntimeError("INTERNAL ERROR: Duplicate field definition")
        FieldDefinition.FIELDS[name] = self


    def __repr__(self):
        """ Return a representation of internal state.
        """
        return "<%s(%r, %r, %r)>" % (self.__class__.__name__, self.valtype, self.name, self.__doc__)

    
    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        return self.valtype(self._accessor(obj) if self._accessor else obj._fields[self.name])


    def __delete__(self, obj):
        raise RuntimeError("Can't delete field %r" % (self.name,))


class ImmutableField(FieldDefinition):
    """ Read-only download item field.
    """

    def __set__(self, obj, val):
        raise RuntimeError("Immutable field %r" % (self.name,))


class ConstantField(ImmutableField):
    """ Read-only download item field with constant value.
    """
    # This can be cached


class DynamicField(ImmutableField):
    """ Read-only download item field with dynamic value.
    """
    # This cannot be cached


class OnDemandField(DynamicField):
    """ Field that is fetched on first access only.
    """

    def __get__(self, obj, cls=None):
        if obj and self.name not in obj._fields:
            obj.fetch(self.name, self._engine_name)
        return super(OnDemandField, self).__get__(obj, cls)


class MutableField(FieldDefinition):
    """ Writable download item field
    """

    def __set__(self, obj, val):
        raise NotImplementedError()


#
# [Somewhat] Generic Engine Interface (abstract base classes)
#
class TorrentProxy(object):
    """ A single download item.
    """
    
    @classmethod
    def add_manifold_attribute(cls, name):
        """ Register a manifold engine attribute.
        
            Return the field or None if "name" isn't a manifold attribute.
        """
        if name.startswith("custom_"):
            try:
                return FieldDefinition.FIELDS[name]
            except KeyError:
                field = OnDemandField(str, name, "custom attribute %r" % name.split('_', 1)[1], 
                    matcher=matching.GlobFilter)
                setattr(cls, name, field)

                return field
        elif name.startswith("kind_") and name[5:].isdigit():
            try:
                return FieldDefinition.FIELDS[name]
            except KeyError:
                limit = int(name[5:].lstrip('0') or '0', 10)
                if limit > 100:
                    raise error.UserError("kind_N: N > 100 in %r" % name)
                field = OnDemandField(set, name, 
                    "kinds of files that make up more than %d%% of this item's size" % limit, 
                    matcher=matching.TaggedAsFilter, formatter=_fmt_tags, 
                    engine_name="kind_%d" % limit)
                setattr(cls, name, field)

                return field


    @classmethod
    def add_custom_fields(cls, *args, **kw):
        """ Add any custom fields defined in the configuration.
        """
        for factory in config.custom_field_factories:
            for field in factory():
                setattr(cls, field.name, field)


    def __init__(self):
        """ Initialize object.
        """
        self._fields = {}


    def __repr__(self):
        """ Return a representation of internal state.
        """
        attrs = set((field.name for field in FieldDefinition.FIELDS.values()
            if field._accessor or field.name in self._fields
        ))
        return "<%s(%s)>" % (self.__class__.__name__, ", ".join(sorted(
            ["%s=%r" % (i, getattr(self, i)) for i in attrs] +
            ["%s=%r" % (i, self._fields[i]) for i in (set(self._fields) - attrs)]
        )))


    def fetch(self, name, engine_name=None):
        """ Get a field on demand.
        
            "engine_name" is the internal name of the client engine.
        """
        raise NotImplementedError()


    def announce_urls(self):
        """ Get a list of all announce URLs.
        """
        raise NotImplementedError()


    def start(self):
        """ (Re-)start downloading or seeding.
        """
        raise NotImplementedError()


    def stop(self):
        """ Stop and close download.
        """
        raise NotImplementedError()


    def ignore(self, flag):
        """ Set ignore status.
        """
        raise NotImplementedError()


    def tag(self, tags):
        """ Add or remove tags.
        """
        raise NotImplementedError()


    def set_throttle(self, name):
        """ Assign to throttle group.
        """
        # TODO: A better way would be to have a MutableField class, i.e. item.throttle = "name"
        raise NotImplementedError()


    def set_custom(self, key, value=None):
        """ Set a custom value. C{key} might have the form "key=value" when value is C{None}.
        """
        raise NotImplementedError()


    def hash_check(self):
        """ Hash check a download.
        """
        raise NotImplementedError()


    def delete(self):
        """ Remove torrent from client.
        """
        raise NotImplementedError()


    def flush(self):
        """ Write volatile data to disk.
        """
        # This can be empty in derived classes

    # Basic fields
    hash = ConstantField(str, "hash", "info hash", matcher=matching.GlobFilter)
    name = ConstantField(fmt.to_unicode, "name", "name (file or root directory)", matcher=matching.GlobFilter)
    size = ConstantField(int, "size", "data size", matcher=matching.ByteSizeFilter)
    prio = OnDemandField(int, "prio", "priority (0=off, 1=low, 2=normal, 3=high)", matcher=matching.FloatFilter)
    tracker = ConstantField(str, "tracker", "first in the list of announce URLs", matcher=matching.GlobFilter,
        accessor=lambda o: o.announce_urls()[0])
    alias = ConstantField(config.map_announce2alias, "alias", "tracker alias or domain",
        matcher=matching.GlobFilter, accessor=operator.attrgetter("tracker"))
    message = OnDemandField(str, "message", "current tracker message", matcher=matching.GlobFilter)

    # State
    is_private = ConstantField(bool, "is_private", "private flag set (no DHT/PEX)?", matcher=matching.BoolFilter, 
        formatter=lambda val: "PRV" if val else "PUB")
    is_open = DynamicField(bool, "is_open", "download open?", matcher=matching.BoolFilter,
        formatter=lambda val: "OPN" if val else "CLS")
    is_active = DynamicField(bool, "is_active", "download active?", matcher=matching.BoolFilter,
        formatter=lambda val: "ACT" if val else "STP")
    is_complete = DynamicField(bool, "is_complete", "download complete?", matcher=matching.BoolFilter,
        formatter=lambda val: "DONE" if val else "PART")
    is_ignored = OnDemandField(bool, "is_ignored", "ignore commands?", matcher=matching.BoolFilter,
        formatter=lambda val: "IGN!" if int(val) else "HEED")
    is_ghost = DynamicField(bool, "is_ghost", "has no data file or directory?", matcher=matching.BoolFilter,
        accessor=lambda o: not os.path.exists(fmt.to_unicode(o._fields["path"])),
        formatter=lambda val: "GHST" if val else "DATA")

    # Paths
    directory = OnDemandField(fmt.to_unicode, "directory", "directory containing download data", matcher=matching.GlobFilter)
    path = DynamicField(fmt.to_unicode, "path", "path to download data", matcher=matching.GlobFilter,
        accessor=lambda o: os.path.expanduser(fmt.to_unicode(o._fields["path"])) if o._fields["path"] else "")
    realpath = DynamicField(fmt.to_unicode, "realpath", "real path to download data", matcher=matching.GlobFilter,
        accessor=lambda o: os.path.realpath(o.path.encode("UTF-8")) if o._fields["path"] else "")
    metafile = ConstantField(fmt.to_unicode, "metafile", "path to torrent file", matcher=matching.GlobFilter,
        accessor=lambda o: os.path.expanduser(fmt.to_unicode(o._fields["metafile"])))
    files = OnDemandField(list, "files", "list of files in this item", 
        matcher=matching.FilesFilter, formatter=_fmt_files)
    fno = OnDemandField(int, "fno", "number of files in this item", matcher=matching.FloatFilter, engine_name="size_files")
    
    # Bandwidth & Data Transfer
    done = OnDemandField(percent, "done", "completion in percent", matcher=matching.FloatFilter)
    ratio = DynamicField(ratio_float, "ratio", "normalized ratio (1:1 = 1.0)", matcher=matching.FloatFilter)
    uploaded = OnDemandField(int, "uploaded", "amount of uploaded data", 
        matcher=matching.ByteSizeFilter, engine_name="up_total")
    xfer = DynamicField(int, "xfer", "transfer rate", matcher=matching.ByteSizeFilter,
        accessor=lambda o: o.fetch("up") + o.fetch("down"))
    down = DynamicField(int, "down", "download rate", matcher=matching.ByteSizeFilter)
    up = DynamicField(int, "up", "upload rate", matcher=matching.ByteSizeFilter)
    throttle = OnDemandField(str, "throttle", "throttle group name (NULL=unlimited, NONE=global)", matcher=matching.GlobFilter,
        accessor=lambda o: o._fields["throttle"] or "NONE")

    # Lifecyle
    loaded = DynamicField(long, "loaded", "time metafile was loaded", matcher=matching.TimeFilter,
        accessor=lambda o: long(o.fetch("custom_tm_loaded") or "0", 10), formatter=fmt.iso_datetime_optional)
    started = DynamicField(long, "started", "time download was FIRST started", matcher=matching.TimeFilter,
        accessor=lambda o: long(o.fetch("custom_tm_started") or "0", 10), formatter=fmt.iso_datetime_optional)
    leechtime = DynamicField(untyped, "leechtime", "time taken from start to completion", matcher=matching.DurationFilter,
        accessor=lambda o: _interval_sum(o.fetch("custom_activations"), end=o.completed, context=o.name)
                        or _duration(o.started, o.completed),
        formatter=_fmt_duration)
    completed = DynamicField(long, "completed", "time download was finished", matcher=matching.TimeFilter,
        accessor=lambda o: long(o.fetch("custom_tm_completed") or "0", 10), formatter=fmt.iso_datetime_optional)
    seedtime = DynamicField(untyped, "seedtime", "total seeding time after completion", matcher=matching.DurationFilter,
        accessor=lambda o: _interval_sum(o.fetch("custom_activations"), start=o.completed, context=o.name)
                           if o.is_complete else None,
        formatter=_fmt_duration)

    # Classification
    tagged = DynamicField(set, "tagged", "has certain tags?", matcher=matching.TaggedAsFilter,
        accessor=lambda o: set(o.fetch("custom_tags").lower().split()), formatter=_fmt_tags)
    views = OnDemandField(set, "views", "views this item is attached to", 
        matcher=matching.TaggedAsFilter, formatter=_fmt_tags, engine_name="=views")
    kind = DynamicField(set, "kind", "ALL kinds of files in this item (the same as kind_0)", 
        matcher=matching.TaggedAsFilter, formatter=_fmt_tags, accessor=lambda o: o.fetch("kind_0"))
    traits = DynamicField(list, "traits", "automatic classification of this item (audio, video, tv, movie, etc.)", 
        matcher=matching.TaggedAsFilter, formatter=lambda v: '/'.join(v or ["misc", "other"]), 
        accessor=lambda o: detect_traits(o))
    # = DynamicField(, "", "")

    # TODO: metafile data cache (sqlite, shelve or maybe .ini)
    # cache data indexed by hash
    # store ctime per cache entry
    # scan metafiles of new hashes not yet in cache
    # on cache read, for unknown hashes setdefault() a purge date, then remove entries after a while
    # clear purge date for known hashes (unloaded and then reloaded torrents)
    # store a version marker and other global metadata in cache under key = None, so it can be upgraded
    # add option to pyroadmin to inspect the cache, mainly for debugging
    
    # TODO: created (metafile creation date, i.e. the bencoded field; same as downloaded if missing; cached by hash)
    # add .age formatter (age = " 1y 6m", " 2w 6d", "12h30m", etc.)



class TorrentView(object):
    """ A view on a subset of torrent items.
    """
  
    def __init__(self, engine, viewname, matcher=None):
        """ Initialize view on torrent items.
        """
        self.engine = engine
        self.viewname = viewname or "main"
        self.matcher = matcher
        self._items = None


    def _fetch_items(self):
        """ Fetch to attribute.
        """
        if self._items is None:
            self._items = list(self.engine.items(self)) 

        return self._items


    def size(self):
        """ Total unfiltered size of view.
        """
        return len(self._fetch_items())


    def items(self):
        """ Get list of download items.
        """
        if self.matcher:
            for item in self._fetch_items():
                if self.matcher.match(item):
                    yield item
        else:
            for item in self._fetch_items():
                yield item


class TorrentEngine(object):
    """ A torrent backend.
    """

    def __init__(self):
        """ Initialize torrent backend engine.
        """
        self.LOG = pymagic.get_class_logger(self)
        self.engine_id = "N/A"          # ID of the instance we're connecting to
        self.engine_software = "N/A"    # Name and version of software


    def load_config(self, namespace=config):
        """ Load engine configuration file.
        """
        raise NotImplementedError()


    def open(self):
        """ Open connection.
        """
        raise NotImplementedError()


    def view(self, viewname, matcher=None):
        """ Get list of download items.
        """
        return TorrentView(self, viewname, matcher)


    def items(self, view=None, prefetch=None):
        """ Get list of download items.
        """
        raise NotImplementedError()


    def show(self, items, view=None):
        """ Visualize a set of items (search result).
        """
        raise NotImplementedError()


#
# Displaying and filtering items
#
class OutputMapping(algo.AttributeMapping):
    """ Map item fields for displaying them.
    """

    @classmethod
    def formatter_help(cls):
        """ Return a list of format specifiers and their documentation.
        """
        result = [("raw", "Switch off the default field formatter.")]

        for name, method in vars(cls).items():
            if name.startswith("fmt_"):
                result.append((name[4:], method.__doc__.strip()))
        
        return result


    def __init__(self, obj, defaults=None):
        """ Store object we want to map, and any default values.

            @param obj: the wrapped object
            @type obj: object 
            @param defaults: default values
            @type defaults: dict
        """
        super(OutputMapping, self).__init__(obj, defaults)

        # add percent sign so we can easily reference it in .ini files
        # (a better way is to use "%%%%" though, so regard this as deprecated)
        # or maybe not deprecated, header queries return '%' now...
        self.defaults.setdefault("pc", '%')


    def fmt_sz(self, intval):
        """ Format a byte sized value.
        """
        return fmt.human_size(intval)


    def fmt_iso(self, dt):
        """ Format a UNIX timestamp to an ISO datetime string.
        """
        return fmt.iso_datetime(dt)

    
    def fmt_delta(self, dt):
        """ Format a UNIX timestamp to a relative delta.
        """
        return fmt.human_duration(float(dt), precision=2, short=True)

    
    def fmt_pc(self, floatval):
        """ Scale a ratio value to percent.
        """
        return round(float(floatval) * 100.0, 2)

    
    def fmt_strip(self, val):
        """ Strip leading and trailing whitespace.
        """
        return str(val).strip()

    
    def fmt_mtime(self, val):
        """ Modification time of a path.
        """
        return os.path.getmtime(val)

    
    def fmt_pathbase(self, val):
        """ Base name of a path.
        """
        return os.path.basename(val or '')

    
    def fmt_pathname(self, val):
        """ Base name of a path, without its extension.
        """
        return os.path.splitext(os.path.basename(val or ''))[0]

    
    def fmt_pathext(self, val):
        """ Extension of a path (including the '.').
        """
        return os.path.splitext(val or '')[1]

    
    def fmt_pathdir(self, val):
        """ Directory containing the given path.
        """
        return os.path.dirname(val or '')

    
    def __getitem__(self, key):
        """ Return object attribute named C{key}. Additional formatting is provided
            by adding modifiers like ".sz" (byte size formatting) to the normal field name.

            If the wrapped object is None, the upper-case C{key} (without any modifiers)
            is returned instead, to allow the formatting of a header line.
        """
        # Check for formatter specifications
        formatter = None
        have_raw = False
        if '.' in key:
            key, formats = key.split('.', 1)
            formats = formats.split('.')

            have_raw = formats[0] == "raw"
            if have_raw:
                formats = formats[1:]
            
            for fmtname in formats:
                try:
                    fmtfunc = getattr(self, "fmt_"+fmtname)
                except AttributeError:
                    raise error.UserError("Unknown formatting spec %r for %r" % (fmtname, key))
                else:
                    formatter = (lambda val, f=fmtfunc, k=formatter: f(k(val))) if formatter else fmtfunc

        # Check for a field formatter
        try:
            field = FieldDefinition.FIELDS[key]
        except KeyError:
            if key not in self.defaults and not TorrentProxy.add_manifold_attribute(key): 
                raise error.UserError("Unknown field %r" % (key,))  
        else:
            if field._formatter and not have_raw:
                formatter = (lambda val, f=formatter: f(field._formatter(val))) if formatter else field._formatter 

        if self.obj is None:
            # Return column name
            return '%' if key == "pc" else key.upper()
        else:
            # Return formatted value
            val = super(OutputMapping, self).__getitem__(key)
            try:
                return formatter(val) if formatter else val
            except (TypeError, ValueError, KeyError, IndexError, AttributeError), exc:
                raise error.LoggableError("While formatting %s=%r: %s" % (key, val, exc))


def validate_field_list(fields, allow_fmt_specs=False, name_filter=None):
    """ Make sure the fields in the given list exist.
    
        @param fields: List of fields (comma-/space-separated if a string).
        @type fields: list or str
        @return: validated field names.
        @rtype: list  
    """
    formats = [i[4:] for i in dir(OutputMapping) if i.startswith("fmt_")]
    
    try:
        fields = [i.strip() for i in fields.replace(',', ' ').split()]
    except AttributeError:
        # Not a string
        pass

    if name_filter:
        fields = [name_filter(name) for name in fields]

    for name in fields:
        if allow_fmt_specs and '.' in name:
            fullname = name
            name, fmtspecs = name.split('.', 1)
            for fmt in fmtspecs.split('.'):
                if fmt not in formats and fmt != "raw": 
                    raise error.UserError("Unknown format specification %r in %r" % (fmt, fullname))
            
        if name not in FieldDefinition.FIELDS and not TorrentProxy.add_manifold_attribute(name):
            raise error.UserError("Unknown field name %r" % (name,))

    return fields


def create_filter(condition):
    """ Create a filter object from a textual condition.
    """
    # Split name from value(s)
    try:
        name, values = condition.split('=', 1)
    except ValueError:
        name, values = "name", condition

    # Try to find field definition
    try:
        field = FieldDefinition.FIELDS[name]
    except KeyError:
        # Is it a custom attribute?
        field = TorrentProxy.add_manifold_attribute(name)
        if not field:
            raise matching.FilterError("Unknown field %r in %r" % (name, condition))  

    if field._matcher is None: 
        raise matching.FilterError("Field %r cannot be used as a filter" % (name,))  

    # Make filters from values
    filters = []
    for value in values.split(','):
        wrapper = None
        if value.startswith('!'):
            wrapper = matching.NegateFilter
            value = value[1:]
        field_matcher = field._matcher(name, value)
        filters.append(wrapper(field_matcher) if wrapper else field_matcher)

    # Return filters
    return matching.CompoundFilterAny(filters) if len(filters) > 1 else filters[0]  


def _tree2str(tree, root=True):
    """ Convert parsed condition tree back to a (printable) string.
    """
    try:
        # Keep strings as they are
        return '' + tree
    except (TypeError, ValueError):
        flat = ' '.join(_tree2str(i, root=False) for i in tree)
        return flat if root else "[ %s ]" % flat
    

def parse_filter_conditions(conditions):
    """ Parse filter conditions.
    
        @param conditions: multiple conditions.
        @type conditions: list or str 
    """
    conditions_text = conditions
    try:
        conditions = conditions.split()
    except AttributeError:
        # Not a string, assume parsed tree
        conditions_text = _tree2str(conditions)

    # Empty list?
    if not conditions:
        raise matching.FilterError("No conditions given at all!")

    # Handle grouping
    if '[' in conditions:
        tree = [[]]
        for term in conditions:
            if term == '[':
                tree.append([]) # new grouping
            elif term == ']':
                subtree = tree.pop()
                if not tree:
                    raise matching.FilterError("Unbalanced brackets, too many closing ']' in condition %r" % (conditions_text,))
                tree[-1].append(subtree) # append finished group to containing level
            else:
                tree[-1].append(term) # append to current level

        if len(tree) > 1:
            raise matching.FilterError("Unbalanced brackets, too many open '[' in condition %r" % (conditions_text,))
        conditions = tree[0]

    # Prepare root matcher
    conditions = list(conditions)
    matcher = matching.CompoundFilterAll()
    if "OR" in conditions:
        root = matching.CompoundFilterAny()
        root.append(matcher)
    else:
        root = matcher

    # Go through conditions and parse them
    for condition in conditions:
        if condition == "OR":
            # Leading OR, or OR OR in sequence?
            if not matcher:
                raise matching.FilterError("Left-hand side of OR missing in %r!" % (conditions_text,))

            # Start next run of AND conditions
            matcher = matching.CompoundFilterAll()
            root.append(matcher)
        elif isinstance(condition, list):
            matcher.append(parse_filter_conditions(condition))
        else:
            matcher.append(create_filter(condition))

    # Trailing OR?
    if not matcher:
        raise matching.FilterError("Right-hand side of OR missing in %r!" % (conditions_text,))

    return root

