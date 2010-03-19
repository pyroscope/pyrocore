# -*- coding: utf-8 -*-
# pylint: disable-msg=I0011
""" PyroCore - Torrent Engine Interface.

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
import os
import operator

from pyrocore import config, error 
from pyrocore.util import pymagic, fmt, algo
from pyrocore.torrent import matching 


#
# Conversion Helpers
#
def ratio_float(intval):
    """ Convert scaled integer ratio to a normalized float.
    """
    return intval / 1000.0


def percent(floatval):
    """ Convert float ratio to a percent value.
    """
    return floatval * 100.0


#
# Field Descriptors
#
class FieldDefinition(object):
    """ Download item field.
    """
    FIELDS = {}

    def __init__(self, valtype, name, doc, accessor=None, matcher=None, formatter=None):
        self.valtype = valtype
        self.name = name
        self.__doc__ = doc
        self._accessor = accessor
        self._matcher = matcher
        self._formatter = formatter

        if name in FieldDefinition.FIELDS:
            raise RuntimeError("INTERNAL ERROR: Duplicate field definition")
        FieldDefinition.FIELDS[name] = self

    
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


class DynamicField(FieldDefinition):
    """ Read-only download item field with dynamic value.
    """


class OnDemandField(DynamicField):
    """ Field that is fetched on first access only.
    """

    def __get__(self, obj, cls=None):
        if obj and self.name not in obj._fields:
            obj.fetch(self.name)
        return super(OnDemandField, self).__get__(obj, cls)


class MutableField(FieldDefinition):
    """ Read-only download item field
    """

    def __set__(self, obj, val):
        raise NotImplementedError()


#
# Generic Engine Interface (abstract base classes)
#
class TorrentProxy(object):
    """ A single download item.
    """

    def __init__(self):
        """ Initialize object.
        """
        self._fields = {}


    def __repr__(self):
        """ Return a representation of internal state.
        """
        attrs = set(FieldDefinition.FIELDS)
        return "<%s(%s)>" % (self.__class__.__name__, ", ".join(sorted(
            ["%s=%r" % (i, getattr(self, i)) for i in attrs] +
            ["%s=%r" % (i, self._fields[i]) for i in (set(self._fields) - attrs)]
        )))


    def fetch(self, name):
        """ Get a field on demand.
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


    def hash_check(self):
        """ Hash check a download.
        """
        raise NotImplementedError()


    # Field definitions
    hash = ImmutableField(str, "hash", "info hash", matcher=matching.GlobFilter)
    name = ImmutableField(fmt.to_unicode, "name", "name (file or root directory)", matcher=matching.GlobFilter)
    is_private = ImmutableField(bool, "is_private", "private flag set (no DHT/PEX)?", matcher=matching.BoolFilter, 
                                formatter=lambda val: "PRV" if val else "PUB")
    is_open = DynamicField(bool, "is_open", "download open?", matcher=matching.BoolFilter,
                           formatter=lambda val: "OPN" if val else "CLS")
    is_complete = DynamicField(bool, "is_complete", "download complete?", matcher=matching.BoolFilter,
                               formatter=lambda val: "DONE" if val else "PART")
    is_ghost = DynamicField(bool, "is_ghost", "has no data file or directory?", matcher=matching.BoolFilter,
                            accessor=lambda o: not os.path.exists(fmt.to_unicode(o._fields["path"])),
                            formatter=lambda val: "GHST" if val else "DATA")
    size = DynamicField(int, "size", "data size", matcher=matching.ByteSizeFilter)
    done = OnDemandField(percent, "done", "completion in percent", matcher=matching.FloatFilter)
    ratio = DynamicField(ratio_float, "ratio", "normalized ratio (1:1 = 1.0)", matcher=matching.FloatFilter)
    xfer = DynamicField(int, "xfer", "transfer rate", matcher=matching.ByteSizeFilter,
                        accessor=lambda o: o._fields["up"] + o._fields["down"])
    down = DynamicField(int, "down", "download rate", matcher=matching.ByteSizeFilter)
    up = DynamicField(int, "up", "upload rate", matcher=matching.ByteSizeFilter)
    path = DynamicField(fmt.to_unicode, "path", "path to download data", matcher=matching.GlobFilter,
                        accessor=lambda o: os.path.expanduser(fmt.to_unicode(o._fields["path"])))
    realpath = DynamicField(fmt.to_unicode, "realpath", "real path to download data", matcher=matching.GlobFilter,
                            accessor=lambda o: os.path.realpath(o.path.encode("UTF-8")))
    metafile = DynamicField(fmt.to_unicode, "metafile", "path to torrent file", matcher=matching.GlobFilter,
                            accessor=lambda o: os.path.expanduser(fmt.to_unicode(o._fields["metafile"])))
    tracker = DynamicField(str, "tracker", "first in the list of announce URLs", matcher=matching.GlobFilter,
                           accessor=lambda o: o.announce_urls()[0])
    alias = DynamicField(config.map_announce2alias, "alias", "tracker alias or domain",
                                 matcher=matching.GlobFilter, accessor=operator.attrgetter("tracker"))
    message = OnDemandField(str, "message", "current tracker message", matcher=matching.GlobFilter)
    prio = OnDemandField(int, "prio", "priority (1=low, 2=normal, 3=high)", matcher=matching.FloatFilter)
    # = DynamicField(, "", "")

    # TODO: metafile data cache (sqlite, shelve or maybe .ini)
    # cache data indexed by hash
    # store ctime per cache entry
    # scan metafiles of new hashes not yet in cache
    # on cache read, for unknown hashes setdefault() a purge date, then remove entries after a while
    # clear purge date for known hashes (unloaded and then reloaded torrents)
    # store a version marker and other global metadata in cache under key = None, so it can be upgraded
    # add option to pyroadmin to inspect the cache, mainly for debugging
    
    # TODO: kind
    # kind = set(all [media?] extensions in the metafile path list; cached by hash)
    # add field type TagField (list of tags) and appropriate matcher 
    
    # TODO: tags
    # list of user-defined tags in a rtorrent custom field
    # e.g. "tags=!manual" to exclude torrents from ratio mgmt etc.

    # TODO: created (metafile creation date, i.e. the bencoded field; same as downloaded if missing; cached by hash)
    # TODO: downloaded (metafile ctime; cached by hash, so the file can be touched)
    # TODO: completed (newest timestamp of the files in the metafile list; cached by hash)
    # add .dt, .isodt and .age formatters (age = " 1y 6m", " 2w 6d", "12h30m", etc.)


class TorrentEngine(object):
    """ A torrent backend.
    """

    def __init__(self):
        """ Initialize torrent backend engine.
        """
        self.LOG = pymagic.get_class_logger(self)
        self.engine_id = "N/A"          # ID of the instance we're connecting to
        self.engine_software = "N/A"    # Name and version of software


    def open(self):
        """ Open connection.
        """
        raise NotImplementedError()


    def items(self):
        """ Get list of download items.
        """
        raise NotImplementedError()


class OutputMapping(algo.AttributeMapping):
    """ Map item fields for displaying them.
    """

    def fmt_sz(self, intval):
        """ Format a byte sized value.
        """
        return fmt.human_size(intval)

    
    def __getitem__(self, key):
        """ Return object attribute named C{key}. Attional formatting is provided
            by adding ".sz" (byte size formmating) to the normal field name.
        """
        # Check for a formatter specification
        formatter = None
        if '.' in key:
            key, fmtname = key.rsplit('.', 1)
            try:
                formatter = getattr(self, "fmt_"+fmtname)
            except AttributeError:
                raise error.UserError("Unknown formatting spec %r for %r" % (fmtname, key))

        # Check for a field formatter
        try:
            field = FieldDefinition.FIELDS[key]
        except KeyError:
            if key not in self.defaults: 
                raise error.UserError("Unknown field %r" % (key,))  
        else:
            if field._formatter:
                formatter = (lambda val, f=formatter: field._formatter(f(val))) if formatter else field._formatter 

        # Return formatted value
        val = super(OutputMapping, self).__getitem__(key)
        return formatter(val) if formatter else val


def validate_field_list(fields):
    """ Make sure the fields in the given list exist.
    
        @param fields: List of fields (comma-/space-separated if a string).
        @type fields: list or str
        @return: validated field names.
        @rtype: list  
    """
    try:
        fields = [i.strip() for i in fields.replace(',', ' ').split()]
    except AttributeError:
        # Not a string
        pass

    for name in fields:
        if name not in FieldDefinition.FIELDS:
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


def parse_filter_conditions(conditions):
    """ Parse filter conditions.
    
        @param conditions: multiple conditions.
        @type conditions: list or str 
    """
    try:
        conditions = conditions.split()
    except AttributeError:
        # Not a string
        pass

    matcher = matching.CompoundFilterAll()
    for condition in conditions:
        matcher.append(create_filter(condition))

    return matcher
