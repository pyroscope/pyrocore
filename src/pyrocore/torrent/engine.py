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
import logging

from pyrocore.engine import filter 

LOG = logging.getLogger(__name__)


#
# Conversion Helpers
#
def unicode_fallback(text):
    """ Return a decoded unicode string.
    """ 
    if not text or isinstance(text, unicode):
        return text

    try:
        # Try UTF-8 first
        return text.decode("UTF-8")
    except UnicodeError:
        try:
            # Then Windows Latin-1
            return text.decode("CP1252")
        except UnicodeError:
            # Give up, return byte string in the hope things work out
            return text


def ratio_float(intval):
    """ Convert scaled integer ratio to a normalized float.
    """
    return intval / 1000.0


#
# Field Descriptors
#
class FieldDefinition(object):
    """ Download item field.
    """
    FIELDS = []

    def __init__(self, valtype, name, doc, accessor=None):
        self.valtype = valtype
        self.name = name
        self.__doc__ = doc
        self._accessor = accessor
        FieldDefinition.FIELDS.append(self)

    
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
        attrs = set(k.name for k in FieldDefinition.FIELDS)
        return "<%s(%s)>" % (self.__class__.__name__, ", ".join(sorted(
            ["%s=%r" % (i, getattr(self, i)) for i in attrs] +
            ["%s=%r" % (i, self._fields[i]) for i in (set(self._fields) - attrs)]
        )))


    def start(self):
        """ (Re-)start downloading or seeding.
        """
        raise NotImplementedError()


    def stop(self):
        """ Stop and close download.
        """
        raise NotImplementedError()


    # Field definitions
    hash = ImmutableField(str, "hash", "info hash")
    name = ImmutableField(unicode_fallback, "name", "name (file or root directory)")
    is_private = ImmutableField(bool, "is_private", "private flag set (no DHT/PEX)?")
    is_open = DynamicField(bool, "is_open", "download open?")
    is_complete = DynamicField(bool, "is_complete", "download complete?")
    ratio = DynamicField(ratio_float, "ratio", "normalized ratio (1:1 = 1.0)")
    xfer = DynamicField(int, "xfer", "transfer rate",
                        lambda o: o._fields["up"] + o._fields["down"])
    down = DynamicField(int, "down", "download rate")
    up = DynamicField(int, "up", "upload rate")
    path = DynamicField(unicode_fallback, "path", "path to download data",
                        lambda o: os.path.expanduser(o._fields["path"]))
    realpath = DynamicField(unicode_fallback, "realpath", "real path to download data",
                            lambda o: os.path.realpath(o._fields["path"]))
    metafile = DynamicField(unicode_fallback, "metafile", "path to torrent file",
                            lambda o: os.path.expanduser(o._fields["metafile"]))
    # = DynamicField(, "", "")

    # kind, tracker, announce, size, age,


class TorrentEngine(object):
    """ A torrent backend.
    """

    def __init__(self):
        """ Initialize torrent backend engine.
        """
        self.log = logging.getLogger(self.__class__.__name__)
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


def create_filter(cls, condition):
    """ Create a filter object from a textual condition.
    """
    try:
        name, values = condition.split('=', 1)
    except ValueError:
        name, values = "name", condition
    return None 
    # raise matching.FilterSyntaxError(" in %r" % (condition,))


