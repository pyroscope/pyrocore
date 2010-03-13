# -*- coding: utf-8 -*-
# pylint: disable-msg=I0011
""" PyroCore - Python Utility Functions.

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
import logging


def import_name(module_spec, name=None):
    """ Import identifier C{name} from module C{module_spec}.

        If name is omitted, C{module_spec} must contain the name after the
        module path, delimited by a colon (like a setuptools entry-point).

        @param module_spec: Fully qualified module name, e.g. C{x.y.z}.
        @param name: Name to import from C{module_spec}.
        @return: Requested object.
        @rtype: object
    """
    if name is None:
        module_spec, name = module_spec.split(':', 1)
    module = __import__(module_spec, globals(), {}, [name])
    return getattr(module, name)


def get_class_logger(obj):
    """ Get a logger specific for the given object's class.
    """
    return logging.getLogger(obj.__class__.__module__ + '.' + obj.__class__.__name__)
