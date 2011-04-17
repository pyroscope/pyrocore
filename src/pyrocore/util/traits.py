""" PyroScope - Classifications.

    Copyright (c) 2010, 2011 The PyroScope Project <pyroscope.project@gmail.com>

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
from collections import defaultdict

from pyrocore import config
from pyrocore.util import os

log = logging.getLogger(__name__)

# Sets of of extensions / kinds
KIND_AUDIO = set(("flac", "mp3", "ogg", "wav", "dts", "ac3", "alac", "wma"))
KIND_VIDEO = set(("avi", "mkv", "m4v", "vob", "mp4", "mpg", "wmv"))
KIND_IMAGE = set(("jpg", "png", "gif", "tif", "bmp", "svg"))
KIND_DOCS = set(("chm", "pdf", "cbr", "cbz", "odt", "ods", "doc", "xls", "ppt"))
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

del i


def get_filetypes(filelist, path=None, size=os.path.getsize):
    """ Get a sorted list of file types and their weight in percent 
        from an iterable of file names.
        
        @return: List of weighted file extensions (no '.'), sorted in descending order
        @rtype: list of (weight, filetype)
    """
    path = path or (lambda _: _)

    # Get total size for each file extension
    histo = defaultdict(int)
    for entry in filelist:
        ext = os.path.splitext(path(entry))[1].lstrip('.').lower()
        if ext and ext[0] == 'r' and ext[1:].isdigit():
            ext = "rar"
        elif ext == "jpeg":
            ext = "jpg"
        elif ext == "mpeg":
            ext = "mpg"
        histo[ext] += size(entry)

    # Normalize values to integer percent
    total = sum(histo.values())
    for ext, val in histo.items():
        histo[ext] = int(val * 100.0 / total + .499)

    return sorted(zip(histo.values(), histo.keys()), reverse=True)


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

    # TODO: Split by "dvdrip", year, etc. to get to the title and then
    # do a imdb / tvdb lookup; cache results, hits for longer, misses
    # for a day at max.

    # No clue
    return None


def detect_traits(name=None, alias=None, filetype=None):
    """ Build traits list from passed attributes.
    
        The result is a list of hierarchical classifiers, the top-level 
        consisting of "audio", "movie", "tv", "video", "document", etc.
        It can be used as a part of completion paths to build directory
        structures.
    """
    result = []
    if filetype:
        filetype = filetype.lstrip('.')

    # Check for "themed" trackers
    theme = config.traits_by_alias.get(alias)
    if alias and theme:
        result = [theme, filetype or "other"]

    # Guess from file extensionn and name
    elif filetype in KIND_AUDIO:
        result = ["audio", filetype]
    elif filetype in KIND_VIDEO:
        result = ["video", filetype]

        contents = name_trait(name)
        if contents:
            result = [contents, filetype]
    elif filetype in KIND_IMAGE:
        result = ["img", filetype]
    elif filetype in KIND_DOCS:
        result = ["docs", filetype]
    elif filetype in KIND_ARCHIVE:
        result = ["misc", filetype]

        contents = name_trait(name)
        if contents:
            result = [contents, filetype]

    return result

