""" PyroScope - Data Formatting.

    Copyright (c) 2009 The PyroScope Project <pyroscope.project@gmail.com>

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

import time
import datetime
import logging

log = logging.getLogger(__name__)


def human_size(size):
    """ Return a human-readable representation of a byte size.
    """
    if isinstance(size, basestring):
        size = int(size, 10)
    
    if size < 0:
        return "-??? bytes"

    if size < 1024:
        return "%4d bytes" % size
    for unit in ("KiB", "MiB", "GiB"):
        size /= 1024.0
        if size < 1024:
            return "%6.1f %s" % (size, unit)

    return "%6.1f GiB" % size


def iso_datetime(dt):
    """ Convert UNIX timestamp to ISO datetime string.
    """
    return datetime.datetime.fromtimestamp(dt).isoformat(' ')[:19]


def iso_datetime_optional(dt):
    """ Convert UNIX timestamp to ISO datetime string, or "never".
    """
    if dt:
        return iso_datetime(dt)
    return "never"


def human_duration(time1, time2=None, precision=0, short=False):
    """ Return a human-readable representation of a time delta.
    """
    if time2 is None:
        time2 = time.time()

    duration = (time1 or 0) - time2
    direction = (
        " ago" if duration < 0 else
        ("+now" if short else " from now") if time2 else ""
    )
    duration = abs(duration)
    parts = [
        ("weeks", duration // (7*86400)),
        ("days", duration // 86400 % 7),
        ("hours", duration // 3600 % 24),
        ("mins", duration // 60 % 60),
        ("secs", duration % 60),
    ]
    
    # Kill leading zero parts
    while len(parts) > 1 and parts[0][1] == 0:
        parts = parts[1:]

    # Limit to # of parts given by precision 
    if precision:
        parts = parts[:precision]

    numfmt = ("%d", "%d"), ("%4d", "%2d")        
    fmt = "%1.1s" if short else " %s"
    sep = " " if short else ", "
    result = sep.join((numfmt[bool(short)][bool(idx)] + fmt) % (val, key[:-1] if val == 1 else key)
        for idx, (key, val) in enumerate(parts)
        if val #or (short and precision)
    ) + direction

    if not time1:
        result = "never" if time2 else "N/A"

    if precision and short:
        return result.rjust(1 + precision*4 + (4 if time2 else 0))
    else:
        return result


def to_unicode(text):
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


def to_console(text):
    """ Return a byte string intended for console output.
    """ 
    if isinstance(text, str):
        # For now, leave byte strings as-is (ignoring possible display problems)
        return text

    # Convert other stuff into an UTF-8 string
    return unicode(text).encode("utf8")
