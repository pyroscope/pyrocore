# -*- coding: utf-8 -*-
# pylint: disable=I0011,R0201
""" Torrent Item Formatting and Filter Rule Parsing.

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

import re
import sys
import json
import operator

from pyrobase import templating
from pyrobase.parts import Bunch

from pyrocore import error, config
from pyrocore.torrent import engine
from pyrocore.util import os, fmt, algo, pymagic


log = pymagic.get_lazy_logger(__name__)


#
# Format specifiers
#
def fmt_sz(intval):
    """ Format a byte sized value.
    """
    try:
        return fmt.human_size(intval)
    except (ValueError, TypeError):
        return "N/A".rjust(len(fmt.human_size(0)))


def fmt_iso(timestamp):
    """ Format a UNIX timestamp to an ISO datetime string.
    """
    try:
        return fmt.iso_datetime(timestamp)
    except (ValueError, TypeError):
        return "N/A".rjust(len(fmt.iso_datetime(0)))


def fmt_duration(duration):
    """ Format a duration value in seconds to a readable form.
    """
    try:
        return fmt.human_duration(float(duration), 0, 2, True)
    except (ValueError, TypeError):
        return "N/A".rjust(len(fmt.human_duration(0, 0, 2, True)))


def fmt_delta(timestamp):
    """ Format a UNIX timestamp to a delta (relative to now).
    """
    try:
        return fmt.human_duration(float(timestamp), precision=2, short=True)
    except (ValueError, TypeError):
        return "N/A".rjust(len(fmt.human_duration(0, precision=2, short=True)))


def fmt_pc(floatval):
    """ Scale a ratio value to percent.
    """
    return round(float(floatval) * 100.0, 2)


def fmt_strip(val):
    """ Strip leading and trailing whitespace.
    """
    return str(val).strip()


def fmt_subst(regex, subst):
    """Replace regex with string."""
    return lambda text: re.sub(regex, subst, text) if text else text


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


def fmt_json(val):
    """ JSON serialization.
    """
    return json.dumps(val, cls=pymagic.JSONEncoder)


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
            except (TypeError, ValueError, KeyError, IndexError, AttributeError) as exc:
                raise error.LoggableError("While formatting %s=%r: %s" % (key, val, exc))


def preparse(output_format):
    """ Do any special processing of a template, and return the result.
    """
    try:
        return templating.preparse(output_format, lambda path: os.path.join(config.config_dir, "templates", path))
    except ImportError as exc:
        if "tempita" in str(exc):
            raise error.UserError("To be able to use Tempita templates, install the 'tempita' package (%s)\n"
                "    Possibly USING THE FOLLOWING COMMAND:\n"
                "        %s/easy_install tempita" % (exc, os.path.dirname(sys.executable)))
        raise


# TODO: All constant stuff should be calculated once, make this a class or something
# Also parse the template only once (possibly in config validation)!
def expand_template(template, namespace):
    """ Expand the given (preparsed) template.
        Currently, only Tempita templates are supported.

        @param template: The template, in preparsed form, or as a string (which then will be preparsed).
        @param namespace: Custom namespace that is added to the predefined defaults
            and takes precedence over those.
        @return: The expanded template.
        @raise LoggableError: In case of typical errors during template execution.
    """
    # Create helper namespace
    formatters = dict((name[4:], method)
        for name, method in globals().items()
        if name.startswith("fmt_")
    )
    helpers = Bunch()
    helpers.update(formatters)

    # Default templating namespace
    variables = dict(h=helpers, c=config.custom_template_helpers)
    variables.update(formatters)  # redundant, for backwards compatibility

    # Provided namespace takes precedence
    variables.update(namespace)

    # Expand template
    try:
        template = preparse(template)
        return template.substitute(**variables)
    except (AttributeError, ValueError, NameError, TypeError) as exc:
        hint = ''
        if "column" in str(exc):
            try:
                col = int(str(exc).split("column")[1].split()[0])
            except (TypeError, ValueError):
                pass
            else:
                hint = "%svVv\n" % (' ' * (col+4))

        content = getattr(template, "content", template)
        raise error.LoggableError("%s: %s in template:\n%s%s" % (
            type(exc).__name__, exc, hint,
            "\n".join("%3d: %s" % (i+1, line) for i, line in enumerate(content.splitlines()))
        ))


def format_item(format_spec, item, defaults=None):
    """ Format an item according to the given output format.
        The format can be gioven as either an interpolation string,
        or a Tempita template (which has to start with "E{lb}E{lb}"),

        @param format_spec: The output format.
        @param item: The object, which is automatically wrapped for interpolation.
        @param defaults: Optional default values.
    """
    template_engine = getattr(format_spec, "__engine__", None)

    # TODO: Make differences between engines transparent
    if template_engine == "tempita" or (not template_engine and format_spec.startswith("{{")):
        # Set item, or field names for column titles
        namespace = dict(headers=not bool(item))
        if item:
            namespace["d"] = item
        else:
            namespace["d"] = Bunch()
            for name in engine.FieldDefinition.FIELDS:
                namespace["d"][name] = name.upper()

            # Justify headers to width of a formatted value
            namespace.update((name[4:], lambda x, m=method: str(x).rjust(len(str(m(0)))))
                for name, method in globals().items()
                if name.startswith("fmt_")
            )

        return expand_template(format_spec, namespace)
    else:
        # Interpolation
        format_spec = getattr(format_spec, "fmt", format_spec)

        if item is None:
            # For headers, ensure we only have string formats
            format_spec = re.sub(
                r"(\([_.a-zA-Z0-9]+\)[-#+0 ]?[0-9]*?)[.0-9]*[diouxXeEfFgG]",
                lambda m: m.group(1) + 's', format_spec)

        return format_spec % OutputMapping(item, defaults)


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
        # Not a string, expecting an iterable
        pass

    if name_filter:
        fields = [name_filter(name) for name in fields]

    for name in fields:
        if allow_fmt_specs and '.' in name:
            fullname = name
            name, fmtspecs = name.split('.', 1)
            for fmtspec in fmtspecs.split('.'):
                if fmtspec not in formats and fmtspec != "raw":
                    raise error.UserError("Unknown format specification %r in %r" % (fmtspec, fullname))

        if name not in engine.FieldDefinition.FIELDS and not engine.TorrentProxy.add_manifold_attribute(name):
            raise error.UserError("Unknown field name %r" % (name,))

    return fields


def validate_sort_fields(sort_fields):
    """ Make sure the fields in the given list exist, and return sorting key.

        If field names are prefixed with '-', sort order is reversed for that field (descending).
    """
    # Allow descending order per field by prefixing with '-'
    descending = set()
    def sort_order_filter(name):
        "Helper to remove flag and memoize sort order"
        if name.startswith('-'):
            name = name[1:]
            descending.add(name)
        return name

    # Split and validate field list
    sort_fields = validate_field_list(sort_fields, name_filter=sort_order_filter)
    log.debug("Sorting order is: %s" % ", ".join([('-' if i in descending else '') + i
        for i in sort_fields]))

    # No descending fields?
    if not descending:
        return operator.attrgetter(*tuple(sort_fields))

    # Need to provide complex key
    class Key(object):
        "Complex sort order key"
        def __init__(self, obj, *args):
            "Remember object to be compared"
            self.obj = obj
        def __lt__(self, other):
            "Compare to other key"
            for field in sort_fields:
                lhs, rhs = getattr(self.obj, field), getattr(other.obj, field)
                if lhs == rhs:
                    continue
                return rhs < lhs if field in descending else lhs < rhs
            return False

    return Key
