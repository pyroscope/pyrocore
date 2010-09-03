""" PyroScope - Classifications.

    Copyright (c) 2010 The PyroScope Project <pyroscope.project@gmail.com>

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
import logging

log = logging.getLogger(__name__)

# Sets of of extensions / kinds
KIND_AUDIO = set(("flac", "mp3", "ogg", "wav", "dts", "ac3", "alac", "wma"))
KIND_VIDEO = set(("avi", "mkv", "m4v", "vob", "mp4", "mpg", "wmv"))
KIND_IMAGE = set(("jpg", "png", "gif", "tif", "bmp", "svg"))
KIND_DOCS = set(("chm", "pdf", "cbz", "odt", "ods", "doc", "xls", "ppt"))
KIND_ARCHIVE = set(("rar", "zip", "tgz", "bz2", "iso", "bin"))

# Regex matchers for names
_VIDEO_EXT = '|'.join(re.escape('.' + i) for i in KIND_VIDEO)
_TV_TRAIL = (
    r"(?:\.(?P<release_tags>PREAIR|READNFO))?"
    r"(?:[._](?P<release>REPACK|PROPER|REAL|REALPROPER|INTERNAL))?"
    r"(?:[._](?P<aspect>WS))?"
    r"(?:[._](?P<format>HDTV|PDTV|DSR|DVDSCR|720p))?"
    r"(?:[._][Xx][Vv2][Ii6][Dd4])?(?:[-.](?P<group>.+?))?(?P<extension>" + _VIDEO_EXT + ")?$"
)
_DEFINITELY_TV = [".%s." % i.lower() for i in ("HDTV", "PDTV", "DSR")]

TV_PATTERNS = [re.compile(i, re.I) for i in (
    ( # Normal TV Episodes
        r"^(?P<show>.+?)\.[sS]?(?P<season>\d{1,2})[xeE](?P<episode>\d{2}(?:eE\d{2})?)"
        r"(?:\.(?P<title>.+[a-z]{1,2}.+?))?"
        + _TV_TRAIL
    ),
    ( # Normal TV Episodes (all-numeric season+episode)
        r"^(?P<show>.+?)\.(?P<season>\d)(?P<episode>\d{2})"
        r"(?:\.(?P<title>.+[a-z]{1,2}.+?))?"
        + _TV_TRAIL
    ),
    ( # Daily Shows
        r"^(?P<show>.+?)\.(?P<date>\d{4}\.\d{2}\.\d{2})"
        r"(?:\.(?P<title>.+[a-z]{1,2}.+?))?"
        + _TV_TRAIL
    ),
    ( # Whole Seasons
        r"^(?P<show>.+?)\.[sS]?(?P<season>\d{1,2})" + _TV_TRAIL
    ),
    ( # Mini Series
        r"^(?P<show>.+?)"
        r"(?:\.(?:(?P<year>\d{4})|Part(?P<part>\d+?)|Pilot)){1,2}"
        r"(?:\.(?P<title>.+[a-z]{1,2}.+?))?"
        + _TV_TRAIL
    ),
    ( # Mini Series (Roman numerals)
        r"^(?P<show>.+?)"
        r"(?:\.Pa?r?t\.(?P<part>[ivxIVX]{1,3}?))"
        r"(?:\.(?P<title>.+[a-z]{1,2}.+?))?"
        + _TV_TRAIL
    ),
)]

MOVIE_PATTERNS = [re.compile(i, re.I) for i in (
    ( # Scene tagged names
        r"^(?P<title>.+?)[. ](?P<year>\d{4})"
        r"(?:[._ ](?P<release>UNRATED|REPACK|INTERNAL|L[iI]M[iI]TED))*"
        r"(?:[._ ](?P<format>480p|576p|720p))?"
        r"(?:[._ ](?P<source>BDRip|BRRip|HDRip|DVDRip|PAL|NTSC))"
        r"(?:[._ ](?P<sound1>AC3|DTS))?"
        r"(?:[._ ][Xx][Vv2][Ii6][Dd4])"
        r"(?:[._ ](?P<sound2>AC3|DTS))?"
        #r"(?:[._ ](?P<channels>6ch))?"
        r"(?:[-.](?P<group>.+?))"
        r"(?P<extension>" + _VIDEO_EXT + ")?$"
    ),
)]


def name_trait(name):
    """ Determine content type from name.
    """
    if not name:
        # Nothing to check against
        return None

    lower_name = name.lower()

    # TV check
    if any(i in lower_name for i in _DEFINITELY_TV):
        return "tv"

    # Regex checks
    for trait, patterns in (("tv", TV_PATTERNS), ("movie", MOVIE_PATTERNS)):
        for pattern in patterns:
            matched = pattern.match(name)
            if matched:
                ##data = matched.groupdict()
                return trait

    # No clue
    return None


def detect_traits(kind, name=None):
    """ Build traits list from given attributes.
    
        The result is a list of hierarchical classifiers, the top-level 
        consisting of "audio", "movie", "tv", "video", "document", etc.
        It can be used as a part of completion paths to build directory
        structures.
    """
    result = []

    if kind in KIND_AUDIO:
        result = ["audio", kind]
    elif kind in KIND_VIDEO:
        result = ["video", kind]

        contents = name_trait(name)
        if contents:
            result = [contents, kind]
    elif kind in KIND_IMAGE:
        result = ["img", kind]
    elif kind in KIND_DOCS:
        result = ["docs", kind]
    elif kind in KIND_ARCHIVE:
        result = ["misc", kind]

        contents = name_trait(name)
        if contents:
            result = [contents, kind]

    return result

