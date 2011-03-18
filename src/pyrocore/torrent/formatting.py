# -*- coding: utf-8 -*-
# pylint: disable=I0011,R0201
""" PyroCore - Torrent Item Formatting and Filter Rule Parsing.

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

from pyrocore import error 
from pyrocore.torrent import engine 
from pyrocore.util import os, fmt, algo


#
# Format specifiers
#
def fmt_sz(intval):
    """ Format a byte sized value.
    """
    try:
        return fmt.human_size(intval)
    except ValueError:
        return "N/A".rjust(len(fmt.human_size(0)))


def fmt_iso(timestamp):
    """ Format a UNIX timestamp to an ISO datetime string.
    """
    return fmt.iso_datetime(timestamp)


def fmt_duration(duration):
    """ Format a duration value in seconds to a readable form.
    """
    try:
        return fmt.human_duration(float(duration), 0, 2, True)
    except ValueError:
        return "N/A".rjust(len(fmt.human_duration(0, 0, 2, True)))


def fmt_delta(timestamp):
    """ Format a UNIX timestamp to a delta (relative to now).
    """
    return fmt.human_duration(float(timestamp), precision=2, short=True)


def fmt_pc(floatval):
    """ Scale a ratio value to percent.
    """
    return round(float(floatval) * 100.0, 2)


def fmt_strip(val):
    """ Strip leading and trailing whitespace.
    """
    return str(val).strip()


def fmt_mtime(val):
    """ Modification time of a path.
    """
    return os.path.getmtime(val) if val else 0


def fmt_pathbase(val):
    """ Base name of a path.
    """
    return os.path.basename(val or '')


def fmt_pathname(val):
    """ Base name of a path, without its extension.
    """
    return os.path.splitext(os.path.basename(val or ''))[0]


def fmt_pathext(val):
    """ Extension of a path (including the '.').
    """
    return os.path.splitext(val or '')[1]


def fmt_pathdir(val):
    """ Directory containing the given path.
    """
    return os.path.dirname(val or '')


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

        for name, method in globals().items():
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
                    fmtfunc = globals()["fmt_"+fmtname]
                except KeyError:
                    raise error.UserError("Unknown formatting spec %r for %r" % (fmtname, key))
                else:
                    formatter = (lambda val, f=fmtfunc, k=formatter: f(k(val))) if formatter else fmtfunc

        # Check for a field formatter
        try:
            field = engine.FieldDefinition.FIELDS[key]
        except KeyError:
            if key not in self.defaults and not engine.TorrentProxy.add_manifold_attribute(key): 
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


def format_item(format, item, defaults=None):
    """ Format an item according to the given output format.
        The format can be gioven as either an interpolation string, 
        or a Tempita template (which has to start with "{{"),

        @param format: The output format. 
        @param item: The object, which is automatically wrapped for interpolation. 
        @param defaults: Optional default values.
    """
    if format.startswith("{{"):
        # Import tempita
        try:
            import tempita
        except ImportError, exc:
            raise error.UserError("To be able to use Tempita templates, (easy_)install the 'tempita' package (%s)" % exc)

        # TODO: All constant stuff should be calculated once, make this a class or something
        # Also parse the template only once (possibly in config validation)!

        # Build namespace, starting with defaults
        namespace = (defaults or {}).copy()

        # Add format specifiers (for headers, disable them)
        namespace.update((name[4:], method if item else lambda x, m=method: str(x).rjust(len(str(m(0)))))
            for name, method in globals().items() 
            if name.startswith("fmt_")
        )

        # Set item, or field names for column titles
        namespace["headers"] = not bool(item)
        if item:
            namespace["d"] = item
        else:
            namespace["d"] = tempita.bunch()
            for name in engine.FieldDefinition.FIELDS:
                namespace["d"][name] = name.upper()

        # Expand template
        return tempita.Template(format).substitute(**namespace)
    else:
        # Interpolation
        if item is None:
            # For headers, ensure we only have string formats
            format = re.sub(
                r"(\([_.a-zA-Z0-9]+\)[-#+0 ]?[0-9]*?)[.0-9]*[diouxXeEfFgG]", 
                lambda m: m.group(1) + 's', format) 

        return format % OutputMapping(item, defaults)


def validate_field_list(fields, allow_fmt_specs=False, name_filter=None):
    """ Make sure the fields in the given list exist.
    
        @param fields: List of fields (comma-/space-separated if a string).
        @type fields: list or str
        @return: validated field names.
        @rtype: list  
    """
    formats = [i[4:] for i in globals() if i.startswith("fmt_")]
    
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
            
        if name not in engine.FieldDefinition.FIELDS and not engine.TorrentProxy.add_manifold_attribute(name):
            raise error.UserError("Unknown field name %r" % (name,))

    return fields
