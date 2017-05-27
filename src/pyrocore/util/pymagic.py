# -*- coding: utf-8 -*-
# pylint: disable=I0011,C0103
""" Python Utility Functions.

    Copyright (c) 2009, 2010 The PyroScope Project <pyroscope.project@gmail.com>
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

import json
import logging
import pkg_resources

from peak.util.proxies import LazyProxy


# Create aliases to make pydev / pylint happy
resource_isdir = pkg_resources.resource_isdir # @UndefinedVariable pylint: disable=E1101
resource_listdir = pkg_resources.resource_listdir # @UndefinedVariable pylint: disable=E1101
resource_string = pkg_resources.resource_string # @UndefinedVariable pylint: disable=E1101


def import_name(module_spec, name=None):
    """ Import identifier C{name} from module C{module_spec}.

        If name is omitted, C{module_spec} must contain the name after the
        module path, delimited by a colon (like a setuptools entry-point).

        @param module_spec: Fully qualified module name, e.g. C{x.y.z}.
        @param name: Name to import from C{module_spec}.
        @return: Requested object.
        @rtype: object
    """
    # Load module
    module_name = module_spec
    if name is None:
        try:
            module_name, name = module_spec.split(':', 1)
        except ValueError:
            raise ValueError("Missing object specifier in %r (syntax: 'package.module:object.attr')" % (module_spec,))

    try:
        module = __import__(module_name, globals(), {}, [name])
    except ImportError as exc:
        raise ImportError("Bad module name in %r (%s)" % (module_spec, exc))

    # Resolve the requested name
    result = module
    for attr in name.split('.'):
        result = getattr(result, attr)

    return result


def get_class_logger(obj):
    """ Get a logger specific for the given object's class.
    """
    return logging.getLogger(obj.__class__.__module__ + '.' + obj.__class__.__name__)


def get_lazy_logger(name):
    """ Return a logger proxy that is lazily initialized.

        This avoids the problems associated with module-level loggers being created
        early (on import), *before* the logging system is properly initialized.
    """
    return LazyProxy(lambda n=name: logging.getLogger(n))


class JSONEncoder(json.JSONEncoder):
    """Custon JSON encoder."""

    def default(self, o):  # pylint: disable=method-hidden
        """Support more object types."""
        if isinstance(o, set):
            return list(sorted(o))
        elif hasattr(o, 'as_dict'):
            return o.as_dict()
        else:
            return super(JSONEncoder, self).default(o)
