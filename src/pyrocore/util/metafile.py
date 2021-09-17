# -*- coding: utf-8 -*-
# pylint: disable=
""" Metafile Support.

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
from __future__ import with_statement
from __future__ import absolute_import
from __future__ import unicode_literals

import re
import sys
import time
import stat
import math
import errno
import pprint
import fnmatch
import hashlib

import six
from six.moves import urllib

import six

from pyrobase import bencode
from pyrobase.parts import Bunch
from pyrocore import config, error
from pyrocore.util import os, fmt, pymagic


# Allowed characters in a metafile filename or path
ALLOWED_ROOT_NAME = re.compile(r"^[^/\\.~][^/\\]*$") # cannot be absolute or ~user, and cannot have path parts
ALLOWED_PATH_NAME = re.compile(r"^(?:~\d+)?[^/\\~][^/\\]*$")

# Character sequences considered secret (roughly, any path part or query parameter
# that looks like an alphanumeric sequence or url-safe base64 string)
PASSKEY_RE = re.compile(r"(?<=[/=])[-_0-9a-zA-Z]{5,64}={0,3}(?=[/&]|$)")

# Non-secret exemptions
PASSKEY_OK = ("announce", "TrackerServlet",)

# List of all standard keys in a metafile
_i = None
METAFILE_STD_KEYS = [_i.split(b'.') for _i in (
    b"announce",
    b"announce-list", # BEP-0012
    b"comment",
    b"created by",
    b"creation date",
    b"encoding",
    b"info",
    b"info.length",
    b"info.name",
    b"info.piece length",
    b"info.pieces",
    b"info.private",
    b"info.files",
    b"info.files.length",
    b"info.files.path",
)]

del _i


def console_progress():
    """ Return a progress indicator for consoles if
        stdout is a tty.
    """
    def progress(totalhashed, totalsize):
        "Helper"
        msg = " " * 30
        if totalhashed < totalsize:
            msg = "%5.1f%% complete" % (totalhashed * 100.0 / totalsize)
        sys.stdout.write(msg + " \r")
        sys.stdout.flush()

    try:
        return progress if sys.stdout.isatty() else None
    except AttributeError:
        return None


def mask_keys(announce_url):
    """ Mask any passkeys (hex sequences) in an announce URL.
    """
    return PASSKEY_RE.sub(
        lambda m: m.group() if m.group() in PASSKEY_OK else u"*" * len(m.group()),
        announce_url)


class MaskingPrettyPrinter(pprint.PrettyPrinter):
    """ A PrettyPrinter that masks strings in the object tree.
    """

    def format(self, obj, context, maxlevels, level):  # pylint: disable=arguments-differ
        """ Mask obj if it looks like an URL, then pass it to the super class.
        """
        if isinstance(obj, six.string_types) and "://" in fmt.to_unicode(obj):
            obj = mask_keys(obj)
        return pprint.PrettyPrinter.format(self, obj, context, maxlevels, level)


def check_info(info):
    """ Validate info dict.

        Raise ValueError if validation fails.
    """
    if not isinstance(info, dict):
        raise ValueError("bad metainfo - not a dictionary")

    pieces = info.get(b"pieces")
    if not isinstance(pieces, six.binary_type) or len(pieces) % 20 != 0:
        raise ValueError("bad metainfo - bad pieces key")

    piece_size = info.get(b"piece length")
    if not isinstance(piece_size, six.integer_types) or piece_size <= 0:
        raise ValueError("bad metainfo - illegal piece length")

    name = info.get(b"name")
    if not isinstance(name, six.string_types):
        raise ValueError("bad metainfo - bad name (type is %r)" % type(name).__name__)
    if not ALLOWED_ROOT_NAME.match(name):
        raise ValueError("name %s disallowed for security reasons" % name)

    if (b"files" in info) == (b"length" in info):
        raise ValueError("single/multiple file mix")

    if b"length" in info:
        length = info.get(b"length")
        if not isinstance(length, six.integer_types) or length < 0:
            raise ValueError("bad metainfo - bad length")
    else:
        files = info.get(b"files")
        if not isinstance(files, (list, tuple)):
            raise ValueError("bad metainfo - bad file list")

        for item in files:
            if not isinstance(item, dict):
                raise ValueError("bad metainfo - bad file value")

            length = item.get(b"length")
            if not isinstance(length, six.integer_types) or length < 0:
                raise ValueError("bad metainfo - bad length")

            path = item.get(b"path")
            if not isinstance(path, (list, tuple)) or not path:
                raise ValueError("bad metainfo - bad path")

            for part in path:
                if not isinstance(part, six.text_type):
                    raise ValueError("bad metainfo - bad path dir")
                part = fmt.to_unicode(part)
                if part == '..':
                    raise ValueError("relative path in %s disallowed for security reasons" % '/'.join(path))
                if part and not ALLOWED_PATH_NAME.match(part):
                    raise ValueError("path %s disallowed for security reasons" % part)

        file_paths = [os.sep.join(item[b"path"]) for item in files]
        if len(set(file_paths)) != len(file_paths):
            raise ValueError("bad metainfo - duplicate path")

    return info


def check_meta(meta):
    """ Validate meta dict.

        Raise ValueError if validation fails.
    """
    if not isinstance(meta, dict):
        raise ValueError("bad metadata - not a dictionary")
    if not isinstance(meta.get(b"announce"), six.string_types):
        raise ValueError("bad announce URL - not a string")
    check_info(meta.get(b"info"))

    return meta


def clean_meta(meta, including_info=False, logger=None):
    """ Clean meta dict. Optionally log changes using the given logger.

        @param logger: If given, a callable accepting a string message.
        @return: Set of keys removed from C{meta}.
    """
    modified = set()

    for key in meta.keys():
        if [key] not in METAFILE_STD_KEYS:
            if logger:
                logger("Removing key %r..." % (key,))
            del meta[key]
            modified.add(key)

    if including_info:
        for key in meta[b"info"].keys():
            if [b"info", key] not in METAFILE_STD_KEYS:
                if logger:
                    logger("Removing key %r..." % ("info." + key,))
                del meta[b"info"][key]
                modified.add(b"info." + key)

        for idx, entry in enumerate(meta[b"info"].get(b"files", [])):
            for key in entry.keys():
                if [b"info", b"files", key] not in METAFILE_STD_KEYS:
                    if logger:
                        logger("Removing key %r from file #%d..." % (key, idx + 1))
                    del entry[key]
                    modified.add(b"info.files." + key)

            # Remove crap that certain PHP software puts in paths
            entry[b"path"] = [i for i in entry[b"path"] if i]

    return modified


def sanitize(meta, diagnostics=False):
    """ Try to fix common problems, especially transcode non-standard string encodings.
    """
    bad_encodings, bad_fields = set(), set()

    def sane_encoding(field, text):
        "Transcoding helper."
        if isinstance(text, six.text_type):
            return text.encode("utf-8")
        for encoding in ('utf-8', meta.get('encoding', None), 'cp1252'):
            if encoding:
                try:
                    u8_text = text.decode(encoding).encode("utf-8")
                    if encoding != 'utf-8':
                        bad_encodings.add(encoding)
                        bad_fields.add(field)
                    return u8_text
                except UnicodeError:
                    continue
        else:
            # Broken beyond anything reasonable
            bad_encodings.add('UNKNOWN/EXOTIC')
            bad_fields.add(field)
            return six.text_type(text, 'utf-8', 'replace').replace('\ufffd', '_').encode("utf-8")

    # Go through all string fields and check them
    for field in (b"comment", b"created by"):
        if field in meta:
            meta[field] = sane_encoding(field, meta[field])

    meta[b"info"][b"name"] = sane_encoding(b'info name', meta[b"info"][b"name"])

    for entry in meta[b"info"].get(b"files", []):
        entry[b"path"] = [sane_encoding(b'file path', i) for i in entry[b"path"]]

    return (meta, bad_encodings, bad_fields) if diagnostics else meta


def assign_fields(meta, assignments, options_debug=False):
    """ Takes a list of C{key=value} strings and assigns them to the
        given metafile. If you want to set nested keys (e.g. "info.source"),
        you have to use a dot as a separator. For exotic keys *containing*
        a dot, double that dot ("dotted..key").

        Numeric values starting with "+" or "-" are converted to integers.

        If just a key name is given (no '='), the field is removed.
    """
    for assignment in assignments:
        assignment = fmt.to_unicode(assignment)
        try:
            if '=' in assignment:
                field, val = assignment.split('=', 1)
            else:
                field, val = assignment, None

            if val and val[0] in "+-" and val[1:].isdigit():
                val = int(val, 10)

            # TODO: Allow numerical indices, and "+" for append
            namespace = meta
            keypath = [i.replace('\0', '.') for i in field.replace('..', '\0').split('.')]
            for key in keypath[:-1]:
                # Create missing dicts as we go...
                namespace = namespace.setdefault(fmt.to_utf8(key), {})
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            if options_debug:
                raise
            raise error.UserError("Bad assignment %r (%s)!" % (assignment, exc))
        else:
            if val is None:
                del namespace[fmt.to_utf8(keypath[-1])]
            else:
                namespace[fmt.to_utf8(keypath[-1])] = fmt.to_utf8(val)

    return meta


def add_fast_resume(meta, datapath):
    """ Add fast resume data to a metafile dict.
    """
    # Get list of files
    files = meta[b"info"].get(b"files", None)
    single = files is None
    if single:
        if os.path.isdir(datapath):
            datapath = os.path.join(datapath, meta[b"info"][b"name"])
        files = [Bunch(
            path=[os.path.abspath(datapath)],
            length=meta[b"info"][b"length"],
        )]

    # Prepare resume data
    resume = meta.setdefault("libtorrent_resume", {})
    resume["bitfield"] = len(meta[b"info"][b"pieces"]) // 20
    resume["files"] = []
    piece_length = meta[b"info"][b"piece length"]
    offset = 0

    for fileinfo in files:
        # Get the path into the filesystem
        filepath = os.sep.join(fileinfo[b"path"])
        if not single:
            filepath = os.path.join(datapath, fmt.to_utf8(filepath.strip(os.sep)))

        # Check file size
        if os.path.getsize(filepath) != fileinfo[b"length"]:
            raise OSError(errno.EINVAL, "File size mismatch for %r [is %d, expected %d]" % (
                filepath, os.path.getsize(filepath), fileinfo[b"length"],
            ))

        # Add resume data for this file
        resume[b"files"].append(dict(
            priority=1,
            mtime=int(os.path.getmtime(filepath)),
            completed=(offset+fileinfo[b"length"]+piece_length-1) // piece_length
                     - offset // piece_length,
        ))
        offset += fileinfo[b"length"]

    return meta


def info_hash(metadata):
    """ Return info hash as a string.
    """
    return hashlib.sha1(bencode.bencode(metadata[b'info'])).hexdigest().upper()


def data_size(metadata):
    """ Calculate the size of a torrent based on parsed metadata.
    """
    info = metadata[b'info']

    if b'length' in info:
        # Single file
        total_size = info[b'length']
    else:
        # Directory structure
        total_size = sum([f[b'length'] for f in info[b'files']])

    return total_size


def checked_open(filename, log=None, quiet=False):
    """ Open and validate the given metafile.
        Optionally provide diagnostics on the passed logger, for
        invalid metafiles, which then just cause a warning but no exception.
        "quiet" can supress that warning.
    """
    with open(filename, "rb") as handle:
        raw_data = handle.read()
    data = bencode.bdecode(raw_data)

    # pylint: disable=
    try:
        check_meta(data)
        if raw_data != bencode.bencode(data):
            raise ValueError("Bad bencoded data - dict keys out of order?") 
    except ValueError as exc:
        if log:
            # Warn about it, unless it's a quiet value query
            if not quiet:
                log.warn("%s: %s" % (filename, exc))
        else:
            raise

    return data


class Metafile(object):
    """ A torrent metafile.
    """

    # Patterns of names to ignore
    IGNORE_GLOB = [
        "core", "CVS", ".*", "*~", "*.swp", "*.tmp", "*.bak",
        "[Tt]humbs.db", "[Dd]esktop.ini", "ehthumbs_vista.db",
        "*.json", "*-thumb.*",
    ]

    # Default min / max piece sizes
    CHUNK_MIN = 2**15
    CHUNK_MAX = 2**24


    def __init__(self, filename, datapath=None):
        """ Initialize metafile.
        """
        self.filename = filename
        self.progress = None
        self.datapath = datapath
        self.ignore = self.IGNORE_GLOB[:]
        self.LOG = pymagic.get_class_logger(self)


    def _get_datapath(self):
        """ Get a valid datapath, else raise an exception.
        """
        if self._datapath is None:
            raise OSError(errno.ENOENT, "You didn't provide any datapath for %r" % self.filename)

        return self._datapath

    def _set_datapath(self, datapath):
        """ Set a datapath.
        """
        if datapath:
            self._datapath = datapath.rstrip(os.sep)
            self._fifo = int(stat.S_ISFIFO(os.stat(self.datapath).st_mode))
        else:
            self._datapath = None
            self._fifo = False

    datapath = property(_get_datapath, _set_datapath)


    def walk(self):
        """ Generate paths in "self.datapath".
        """
        # FIFO?
        if self._fifo:
            if self._fifo > 1:
                raise RuntimeError("INTERNAL ERROR: FIFO read twice!")
            self._fifo += 1

            # Read paths relative to directory containing the FIFO
            with open(self.datapath, "r") as fifo:
                while True:
                    relpath = fifo.readline().rstrip('\n')
                    if not relpath: # EOF?
                        break
                    self.LOG.debug("Read relative path %r from FIFO..." % (relpath,))
                    yield os.path.join(os.path.dirname(self.datapath), relpath)

            self.LOG.debug("FIFO %r closed!" % (self.datapath,))

        # Directory?
        elif os.path.isdir(self.datapath):
            # Walk the directory tree
            for dirpath, dirnames, filenames in os.walk(self.datapath): #, followlinks=True):
                # Don't scan blacklisted directories
                for bad in dirnames[:]:
                    if any(fnmatch.fnmatch(bad, pattern) for pattern in self.ignore):
                        dirnames.remove(bad)

                # Yield all filenames that aren't blacklisted
                for filename in filenames:
                    if not any(fnmatch.fnmatch(filename, pattern) for pattern in self.ignore):
                        #yield os.path.join(dirpath[len(self.datapath)+1:], filename)
                        yield os.path.join(dirpath, filename)

        # Single file
        else:
            # Yield the filename
            yield self.datapath


    def _calc_size(self):
        """ Get total size of "self.datapath".
        """
        return sum(os.path.getsize(filename)
            for filename in self.walk()
        )


    def _make_info(self, piece_size, progress, walker, piece_callback=None):
        """ Create info dict.
        """
        # These collect the file descriptions and piece hashes
        file_list = []
        pieces = []

        # Initialize progress state
        hashing_secs = time.time()
        totalsize = -1 if self._fifo else self._calc_size()
        totalhashed = 0

        # Start a new piece
        sha1sum = hashlib.sha1()
        done = 0
        filename = None

        # Hash all files
        for filename in walker:
            # Assemble file info
            filesize = os.path.getsize(filename)
            filepath = filename[len(os.path.dirname(self.datapath) if self._fifo else self.datapath):].lstrip(os.sep)
            file_list.append({
                b"length": filesize,
                b"path": [x for x in fmt.to_unicode(filepath).replace(os.sep, '/').split('/')],
            })
            self.LOG.debug("Hashing %r, size %d..." % (filename, filesize))

            # Open file and hash it
            fileoffset = 0
            handle = open(filename, "rb")
            try:
                while fileoffset < filesize:
                    # Read rest of piece or file, whatever is smaller
                    chunk = handle.read(min(filesize - fileoffset, piece_size - done))
                    sha1sum.update(chunk) # bogus pylint: disable=E1101
                    done += len(chunk)
                    fileoffset += len(chunk)
                    totalhashed += len(chunk)

                    # Piece is done
                    if done == piece_size:
                        pieces.append(sha1sum.digest()) # bogus pylint: disable=E1101
                        if piece_callback:
                            piece_callback(filename, pieces[-1])

                        # Start a new piece
                        sha1sum = hashlib.sha1()
                        done = 0

                    # Report progress
                    if progress:
                        progress(totalhashed, totalsize)
            finally:
                handle.close()

        # Add hash of partial last piece
        if done > 0:
            pieces.append(sha1sum.digest()) # bogus pylint: disable=E1103
            if piece_callback:
                piece_callback(filename, pieces[-1])

        # Build the meta dict
        metainfo = {
            b"pieces": b"".join(pieces),
            b"piece length": piece_size,
            b"name": os.path.basename(self.datapath),
        }

        # Handle directory/FIFO vs. single file
        if self._fifo or os.path.isdir(self.datapath):
            metainfo[b"files"] = file_list
        else:
            metainfo[b"length"] = totalhashed

        hashing_secs = time.time() - hashing_secs
        self.LOG.info("Hashing of %s took %.1f secs (%s/s)" % (
            fmt.human_size(totalhashed).strip(), hashing_secs, fmt.human_size(totalhashed / hashing_secs).strip(),
        ))

        # Return validated info dict
        return check_info(metainfo), totalhashed


    def _make_meta(self, tracker_url, root_name, private, progress, chunk_min, chunk_max):
        """ Create torrent dict.
        """
        # Calculate piece size
        if self._fifo:
            # TODO we need to add a (command line) param, probably for total data size
            # for now, always 1MB
            piece_size_exp = 20
        else:
            total_size = self._calc_size()
            if total_size:
                piece_size_exp = int(math.log(total_size) / math.log(2)) - 9
            else:
                piece_size_exp = 0

        chunk_min = chunk_min or self.CHUNK_MIN
        chunk_max = chunk_max or self.CHUNK_MAX
        piece_size = min(max(chunk_min, 2 ** piece_size_exp), chunk_max)
        del piece_size_exp  # make unbounded value unavailable

        # Build info hash
        info, totalhashed = self._make_info(piece_size, progress, self.walk() if self._fifo else sorted(self.walk()))

        # Enforce unique hash per tracker
        info[b"x_cross_seed"] = hashlib.md5(tracker_url.encode('utf-8')).hexdigest()

        # Set private flag
        if private:
            info[b"private"] = 1

        # Freely chosen root name (default is basename of the data path)
        if root_name:
            info[b"name"] = root_name

        # Torrent metadata
        meta = {
            b"info": info,
            b"announce": tracker_url.strip(),
        }

        #XXX meta["encoding"] = "UTF-8"

        # Return validated meta dict
        return check_meta(meta), totalhashed


    def create(self, datapath, tracker_urls, comment=None, root_name=None,
                     created_by=None, private=False, no_date=False, progress=None,
                     callback=None, chunk_min=0, chunk_max=0):
        """ Create a metafile with the path given on object creation.
            Returns the last metafile dict that was written (as an object, not bencoded).
        """
        if datapath:
            self.datapath = datapath

        try:
            tracker_urls = ['' + tracker_urls]
        except TypeError:
            tracker_urls = list(tracker_urls)
        multi_mode = len(tracker_urls) > 1

        # TODO add optimization so the hashing happens only once for multiple URLs!
        for tracker_url in tracker_urls:
            # Lookup announce URLs from config file
            try:
                if urllib.parse.urlparse(tracker_url).scheme:
                    tracker_alias = urllib.parse.urlparse(tracker_url).netloc.split(':')[0].split('.')
                    tracker_alias = tracker_alias[-2 if len(tracker_alias) > 1 else 0]
                else:
                    tracker_alias, tracker_url = config.lookup_announce_alias(tracker_url)
                    tracker_url = tracker_url[0]
            except (KeyError, IndexError):
                raise error.UserError("Bad tracker URL %r, or unknown alias!" % (tracker_url,))

            # Determine metafile name
            output_name = self.filename
            if multi_mode:
                # Add 2nd level of announce URL domain to metafile name
                output_name = list(os.path.splitext(output_name))
                try:
                    output_name[1:1] = '-' + tracker_alias
                except (IndexError,):
                    self.LOG.error("Malformed announce URL %r, skipping!" % (tracker_url,))
                    continue
                output_name = ''.join(output_name)

            # Hash the data
            self.LOG.info("Creating %r for %s %r..." % (
                output_name, "filenames read from" if self._fifo else "data in", self.datapath,
            ))
            meta, _ = self._make_meta(tracker_url, root_name, private, progress, chunk_min, chunk_max)

            # Add optional fields
            if comment:
                meta[b"comment"] = comment
            if created_by:
                meta[b"created by"] = created_by
            if not no_date:
                meta[b"creation date"] = int(time.time())
            if callback:
                callback(meta)

            # Write metafile to disk
            self.LOG.debug("Writing %r..." % (output_name,))
            bencode.bwrite(output_name, meta)

        return meta


    def check(self, metainfo, datapath, progress=None):
        """ Check piece hashes of a metafile against the given datapath.

            Return ``True`` when OK.
        """
        if datapath:
            self.datapath = datapath

        def check_piece(filename, piece):
            "Callback for new piece"
            if piece != metainfo[b"info"][b"pieces"][check_piece.piece_index:check_piece.piece_index+20]:
                self.LOG.warn("Piece #%d: Hashes differ in file %r" % (check_piece.piece_index//20, filename))
            check_piece.piece_index += 20
        check_piece.piece_index = 0

        datameta, _ = self._make_info(int(metainfo[b"info"][b"piece length"]), progress,
            [datapath] if b"length" in metainfo[b"info"] else
            (os.path.join(*([datapath] + i[b"path"])) for i in metainfo[b"info"][b"files"]),
            piece_callback=check_piece
        )
        return datameta[b"pieces"] == metainfo[b"info"][b"pieces"]


    def listing(self, masked=True):
        """ List torrent info & contents. Returns a list of formatted lines.
        """
        # Assemble data
        metainfo = bencode.bread(self.filename)
        bad_encodings = []
        bad_fields = []
        if six.PY2: #PY3 knows it's data
            metainfo, bad_encodings, bad_fields = sanitize(metainfo, diagnostics=True)
        announce = metainfo[b'announce']
        info = metainfo[b'info']
        infohash = hashlib.sha1(bencode.bencode(info))

        total_size = data_size(metainfo)
        piece_length = info[b'piece length']
        piece_number, last_piece_length = divmod(total_size, piece_length)

        # Build result
        result = [
            "NAME %s" % (os.path.basename(fmt.to_unicode(self.filename))),
            "SIZE %s (%i * %s + %s)" % (
                fmt.human_size(total_size).strip(),
                piece_number, fmt.human_size(piece_length).strip(),
                fmt.human_size(last_piece_length).strip(),
            ),
            "META %s (pieces %s %.1f%%)" % (
                fmt.human_size(os.path.getsize(self.filename)).strip(),
                fmt.human_size(len(info[b"pieces"])).strip(),
                100.0 * len(info[b"pieces"]) / os.path.getsize(self.filename),
            ),
            "HASH %s" % (infohash.hexdigest().upper()),
            "URL  %s" % (mask_keys if masked else str)(announce),
            "PRV  %s" % ("YES (DHT/PEX disabled)" if info.get(b"private") else "NO (DHT/PEX enabled)"),
            "TIME %s" % ("N/A" if b"creation date" not in metainfo else
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(metainfo[b"creation date"]))
            ),
        ]

        for label, key in (("BY  ", b"created by"), ("REM ", b"comment")):
            if key in metainfo:
                result.append("%s %s" % (label, metainfo.get(key, "N/A")))

        result.extend([
            "",
            "FILE LISTING%s" % ("" if b'length' in info else " [%d file(s)]" % len(info[b'files']),),
        ])
        if b'length' in info:
            # Single file
            result.append("%-69s%9s" % (
                    fmt.to_unicode(info[b'name']),
                    fmt.human_size(total_size),
            ))
        else:
            # Directory structure
            result.append("%s/" % fmt.to_unicode(info[b'name']))
            oldpaths = [None] * 99
            for entry in info[b'files']:
                # Remove crap that certain PHP software puts in paths
                entry_path = [fmt.to_unicode(i) for i in entry[b"path"] if i]

                for idx, item in enumerate(entry_path[:-1]):
                    if item != oldpaths[idx]:
                        result.append("%s%s/" % (' ' * (4*(idx+1)), item))
                        oldpaths[idx] = item
                result.append("%-69s%9s" % (
                    ' ' * (4*len(entry_path)) + entry_path[-1],
                    fmt.human_size(entry[b'length']),
                ))

        if bad_encodings:
            result.extend([
                "",
                "WARNING: Bad encoding(s) {} in these fields: {}"
                .format(', '.join(sorted(bad_encodings)), ', '.join(sorted(bad_fields))),
                "Use the --raw option to inspect these encoding issues.",
            ])

        return result
