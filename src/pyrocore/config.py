# -*- coding: utf-8 -*-
# pylint: disable-msg=I0011
""" PyroCore - Configuration.

    For details, see http://code.google.com/p/pyroscope/wiki/UserConfiguration

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
from pyrocore.util.types import Bunch


def lookup_announce_alias(name):
    """ Get canonical alias name and announce URL list for the given alias.
    """
    for alias, urls in announce.items():
        if alias.lower() == name.lower():
            return alias, urls

    raise KeyError("Unknown alias %s" % (name,))


def map_announce2alias(url):
    """ Get tracker alias for announce URL, and if none is defined, the 2nd level domain.
    """
    import urlparse

    parts = urlparse.urlparse(url)
    server = urlparse.urlunparse((parts.scheme, parts.netloc, "/", None, None, None))

    # Try to find an alias and return its label
    for alias, urls in announce.items():
        if any(i.startswith(server) for i in urls):
            return alias

    # Return 2nd level domain name if no alias found
    try:
        return '.'.join(parts.netloc.split(':')[0].split('.')[-2:])
    except IndexError:
        return parts.netloc


# Remember predefined names
_PREDEFINED = tuple(_ for _ in globals() if not _.startswith('_'))

# Set some defaults to shut up pydev / pylint
scgi_local = ""
engine = Bunch(open=lambda: None)
output_format = ""
action_format = ""
sort_fields = ""
announce = {}
