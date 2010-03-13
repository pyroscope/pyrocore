# -*- coding: utf-8 -*-
# pylint: disable-msg=I0011
""" PyroCore - Torrent Item Filters.

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

from pyrocore import error
from pyrocore.engine import base

LOG = logging.getLogger(__name__)


class FilterSyntaxError(error.UserError):
    """ Syntax error in filter.
    """


class Filter(object):
    """ Base class for all filters.
    """

    def match(self, item):
        """ Return True if filter matches item.
        """
        raise NotImplementedError()


class CompoundFilter(Filter, list):
    """ List of filters that must all match.
    """

    def match(self, item):
        """ Return True if filter matches item.
        """
        return all(i.match(item) for i in self)
