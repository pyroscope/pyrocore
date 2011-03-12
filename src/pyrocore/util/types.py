""" PyroCore - Generic Objects.

    Copyright (c) 2009, 2010 The PyroScope Project <pyroscope.project@gmail.com>

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
from collections import defaultdict


class Bunch(dict):
    """ Generic attribute container that also is a dict.
    """

    def __getattr__(self, name):
        try:
            return dict.__getattribute__(self, name)
        except AttributeError:
            try:
                return self[name]
            except KeyError:
                raise AttributeError("Bunch has no attribute %r in %s" % (
                    name, ', '.join(map(repr, self.keys()))
                ))


    def __setattr__(self, name, value):
        self[name] = value


    def __repr__(self):
        return "Bunch(%s)" % ", ".join(
            sorted("%s=%r" % attr for attr in self.items())
        )

class DefaultBunch(Bunch, defaultdict):
    """ Generic attribute container that also is a dict.
    """
