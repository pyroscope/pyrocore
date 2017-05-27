# -*- coding: utf-8 -*-
# pylint: disable=
""" Torrent Engine Interface.

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
from __future__ import absolute_import
from __future__ import unicode_literals

import re
import time
import operator
from collections import defaultdict

from pyrocore import config, error
from pyrocore.util import os, pymagic, fmt, traits, matching, metafile, xmlrpc


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


def _interval_split(interval, only=None, context=None, event_re=re.compile("[A-Z][0-9]+")):
    """ Split C{interval} into a series of event type and timestamp tuples.
        An exaple of the input is "R1283008245P1283008268".
        Returns events in reversed order (latest first).
    """
    def split_event(event):
        "Helper to parse events."
        kind, val = event[:1], event[1:]
        try:
            return kind, float(val)
        except (TypeError, ValueError):
            return None, 0

    if hasattr(interval, "fetch"):
        interval = interval.fetch("custom_activations")
    ##import sys; print >>sys.stderr, "!!!!!isplit", interval, event_re.findall(interval)

    return list(reversed([split_event(i) for i in event_re.findall(interval) if not only or i.startswith(only)]))


def _interval_sum(interval, start=None, end=None, context=None):
    """ Return sum of intervals between "R"esume and "P"aused events
        in C{interval}, optionally limited by a time window defined
        by C{start} and C{end}. Return empty list if there's no sensible
        information.

        C{interval} is a series of event types and timestamps,
        e.g. "R1283008245P1283008268".
    """
    end = float(end) if end else time.time()
    events = _interval_split(interval, context=context)
    result = []
    ##import sys; print >>sys.stderr, "!!!!!isum", interval.fetch("custom_activations"), events, start, end

    while events:
        event, resumed = events.pop()
        ##print "~~~~~~~~~~", context, event, resumed

        if event != "R":
            # Ignore other events
            continue
        resumed = max(resumed, start or resumed)

        if events: # Further events?
            if not events[-1][0] == "P":
                continue # If not followed by "P", it's not a valid interval
            _, paused = events.pop()
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
    pad = ['\uFFFE'] * depth

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
                if dirname == '\uFFFE':
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

    @classmethod
    def lookup(cls, name):
        """ Try to find field C{name}.

            @return: Field descriptions, see C{matching.ConditionParser} for details.
        """
        try:
            field = cls.FIELDS[name]
        except KeyError:
            # Is it a custom attribute?
            field = TorrentProxy.add_manifold_attribute(name)

        return {"matcher": field._matcher} if field else None


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

            @return: field definition object, or None if "name" isn't a manifold attribute.
        """
        if name.startswith("custom_"):
            try:
                return FieldDefinition.FIELDS[name]
            except KeyError:
                field = OnDemandField(str, name, "custom attribute %r" % name.split('_', 1)[1],
                    matcher=matching.PatternFilter)
                setattr(cls, name, field) # add field to all proxy objects

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
        def mask(key, val):
            'helper to hide sensitive stuff'
            if key in ('tracker', 'custom_m_alias'):
                return key, metafile.mask_keys(val)
            else:
                return key, val

        attrs = set((field.name for field in FieldDefinition.FIELDS.values()
            if field._accessor or field.name in self._fields
        ))
        return "<%s(%s)>" % (self.__class__.__name__, ", ".join(sorted(
            ["%s=%r" % mask(i, getattr(self, i)) for i in attrs] +
            ["%s=%r" % mask(i, self._fields[i]) for i in (set(self._fields) - attrs)]
        )))


    def fetch(self, name, engine_name=None):
        """ Get a field on demand.

            "engine_name" is the internal name of the client engine.
        """
        raise NotImplementedError()


    def datapath(self):
        """ Get an item's data path.
        """
        raise NotImplementedError()


    def announce_urls(self, default=[]):  # pylint: disable=dangerous-default-value
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
    hash = ConstantField(str, "hash", "info hash", matcher=matching.PatternFilter)
    name = ConstantField(fmt.to_unicode, "name", "name (file or root directory)", matcher=matching.PatternFilter)
    size = ConstantField(int, "size", "data size", matcher=matching.ByteSizeFilter)
    prio = OnDemandField(int, "prio", "priority (0=off, 1=low, 2=normal, 3=high)", matcher=matching.FloatFilter,
        formatter=lambda val: "X- +"[val])
    tracker = ConstantField(str, "tracker", "first in the list of announce URLs", matcher=matching.PatternFilter,
        accessor=lambda o: (o.announce_urls(default=[None]) or [None])[0])
    alias = ConstantField(config.map_announce2alias, "alias", "tracker alias or domain",
        matcher=matching.PatternFilter, accessor=lambda o: o._memoize("alias", getattr, o, "tracker"))
        #matcher=matching.PatternFilter, accessor=operator.attrgetter("tracker"))
    message = OnDemandField(fmt.to_unicode, "message", "current tracker message", matcher=matching.PatternFilter)

    # State
    is_private = ConstantField(bool, "is_private", "private flag set (no DHT/PEX)?", matcher=matching.BoolFilter,
        formatter=lambda val: "PRV" if val else "PUB")
    is_open = DynamicField(bool, "is_open", "download open?", matcher=matching.BoolFilter,
        formatter=lambda val: "OPN" if val else "CLS")
    is_active = DynamicField(bool, "is_active", "download active?", matcher=matching.BoolFilter,
        formatter=lambda val: "ACT" if val else "STP")
    is_complete = DynamicField(bool, "is_complete", "download complete?", matcher=matching.BoolFilter,
        formatter=lambda val: "DONE" if val else "PART")
    is_multi_file = OnDemandField(bool, "is_multi_file", "single- or multi-file download?", matcher=matching.BoolFilter,
        formatter=lambda val: "DIR " if val else "FILE")
    is_ignored = OnDemandField(bool, "is_ignored", "ignore commands?", matcher=matching.BoolFilter,
        formatter=lambda val: "IGN!" if int(val) else "HEED")
    is_ghost = DynamicField(bool, "is_ghost", "has no data file or directory?", matcher=matching.BoolFilter,
        accessor=lambda o: not os.path.exists(o.datapath()) if o.datapath() else None,
        formatter=lambda val: "GHST" if val else "DATA")

    # Paths
    """ Shining a light on the naming and paths mess:

        hash=xxx
        for i in d.name d.base_filename d.base_path d.directory d.directory_base d.is_multi_file; do \
            echo -n "$(printf '%20.20s ' $i)"; rtxmlrpc $i $hash
        done

        Basics:
            * d.base_filename is always the basename of d.base_path
            * d.directory_base and d.directory are always the same
            * d.base_filename and d.base_path are empty on closed items, after a restart, i.e. not too useful (since 0.9.1 or so)

        Behaviour of d.directory.set + d.directory_base.set (tested with 0.9.4):
            * d.base_path always remains unchanged, and item gets closed
            * d.start sets d.base_path if resume data ok
            * single:
                * d.directory[_base].set → d.name NEVER appended (only in d.base_path)
                * after start, d.base_path := d.directory/d.name
            * multi:
                * d.directory.set → d.name is appended
                * d.directory_base.set → d.name is NOT appended (i.e. item renamed to last path part)
                * after start, d.base_path := d.directory

        Making sense of it (trying to at least):
            * d.directory is *always* a directory (thus, single items auto-append d.name in d.base_path and cannot be renamed)
            * d.directory_base.set means set path PLUS basename together for a multi item (thus allowing a rename)
            * only d.directory.set behaves consistently for single+multi, regarding the end result in d.base_path
    """
    directory = OnDemandField(fmt.to_unicode, "directory", "directory containing download data", matcher=matching.PatternFilter)
    path = DynamicField(fmt.to_unicode, "path", "path to download data", matcher=matching.PatternFilter,
        accessor=lambda o: o.datapath())
    realpath = DynamicField(fmt.to_unicode, "realpath", "real path to download data", matcher=matching.PatternFilter,
        accessor=lambda o: os.path.realpath(o.datapath()))
    metafile = ConstantField(fmt.to_unicode, "metafile", "path to torrent file", matcher=matching.PatternFilter,
        accessor=lambda o: os.path.expanduser(fmt.to_unicode(o._fields["metafile"])))
    sessionfile = ConstantField(fmt.to_unicode, "sessionfile", "path to session file", matcher=matching.PatternFilter,
        accessor=lambda o: os.path.expanduser(fmt.to_unicode(o.fetch("session_file"))))
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
    throttle = OnDemandField(str, "throttle", "throttle group name (NULL=unlimited, NONE=global)", matcher=matching.PatternFilter,
        accessor=lambda o: o._fields["throttle"] or "NONE")

    # Lifecyle
    loaded = DynamicField(int, "loaded", "time metafile was loaded", matcher=matching.TimeFilterNotNull,
        accessor=lambda o: int(o.fetch("custom_tm_loaded") or "0", 10), formatter=fmt.iso_datetime_optional)
    started = DynamicField(int, "started", "time download was FIRST started", matcher=matching.TimeFilterNotNull,
        accessor=lambda o: int(o.fetch("custom_tm_started") or "0", 10), formatter=fmt.iso_datetime_optional)
    leechtime = DynamicField(untyped, "leechtime", "time taken from start to completion", matcher=matching.DurationFilter,
        accessor=lambda o: _interval_sum(o, end=o.completed, context=o.name)
                        or _duration(o.started, o.completed),
        formatter=_fmt_duration)
    completed = DynamicField(int, "completed", "time download was finished", matcher=matching.TimeFilterNotNull,
        accessor=lambda o: int(o.fetch("custom_tm_completed") or "0", 10), formatter=fmt.iso_datetime_optional)
    seedtime = DynamicField(untyped, "seedtime", "total seeding time after completion", matcher=matching.DurationFilter,
        accessor=lambda o: _interval_sum(o, start=o.completed, context=o.name)
                           if o.is_complete else None,
        formatter=_fmt_duration)
    active = DynamicField(int, "active", "last time a peer was connected", matcher=matching.TimeFilter,
        accessor=lambda o: int(o.fetch("last_active") or 0), formatter=fmt.iso_datetime_optional)
    stopped = DynamicField(int, "stopped", "time download was last stopped or paused", matcher=matching.TimeFilterNotNull,
        accessor=lambda o: (_interval_split(o, only='P', context=o.name) + [(0, 0)])[0][1], formatter=fmt.iso_datetime_optional)

    # Classification
    tagged = DynamicField(set, "tagged", "has certain tags? (not related to the 'tagged' view)",
        matcher=matching.TaggedAsFilter,
        accessor=lambda o: set(o.fetch("custom_tags").lower().split()),
        formatter=_fmt_tags)
    views = OnDemandField(set, "views", "views this item is attached to",
        matcher=matching.TaggedAsFilter, formatter=_fmt_tags, engine_name="=views")
    kind = DynamicField(set, "kind", "ALL kinds of files in this item (the same as kind_0)",
        matcher=matching.TaggedAsFilter, formatter=_fmt_tags, accessor=lambda o: o.fetch("kind_0"))
    traits = DynamicField(list, "traits", "automatic classification of this item (audio, video, tv, movie, etc.)",
        matcher=matching.TaggedAsFilter, formatter=lambda v: '/'.join(v or ["misc", "other"]),
        accessor=detect_traits)
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
        self.viewname = viewname or "default"
        self.matcher = matcher
        self._items = None


    def _fetch_items(self):
        """ Fetch to attribute.
        """
        if self._items is None:
            self._items = list(self.engine.items(self))

        return self._items


    def _check_hash_view(self):
        """ Return infohash if view name refers to a single item, else None.
        """
        infohash = None
        if self.viewname.startswith('#'):
            infohash = self.viewname[1:]
        elif len(self.viewname) == 40:
            try:
                int(self.viewname, 16)
            except (TypeError, ValueError):
                pass
            else:
                infohash = self.viewname
        return infohash


    def size(self):
        """ Total unfiltered size of view.
        """
        #return len(self._fetch_items())
        if self._check_hash_view():
            return 1
        else:
            return self.engine.open().view.size(xmlrpc.NOHASH, self.viewname)


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


    def load_config(self, namespace=None, rcfile=None):
        """ Load engine configuration file.
        """
        raise NotImplementedError()


    def open(self):
        """ Open connection.
        """
        raise NotImplementedError()


    def log(self, msg):
        """ Log a message in the torrent client.
        """
        raise NotImplementedError()


    def view(self, viewname, matcher=None):
        """ Get list of download items.
        """
        return TorrentView(self, viewname, matcher)


    def items(self, view=None, prefetch=None, cache=True):
        """ Get list of download items.
        """
        raise NotImplementedError()


    def show(self, items, view=None):
        """ Visualize a set of items (search result), and return the view name.
        """
        raise NotImplementedError()


    def group_by(self, fields, items=None):
        """ Returns a dict of lists of items, grouped by the given fields.

            ``fields`` can be a string (one field) or an iterable of field names.
        """
        result = defaultdict(list)
        if items is None:
            items = self.items()

        try:
            key = operator.attrgetter(fields + '')
        except TypeError:
            def key(obj, names=tuple(fields)):
                'Helper to return group key tuple'
                return tuple(getattr(obj, x) for x in names)

        for item in items:
            result[key(item)].append(item)

        return result
