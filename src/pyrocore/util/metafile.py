""" PyroCore - Metafile Support.

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

import os
import re
import time
import math
import fnmatch
import hashlib
import logging

from pyrocore.util import bencode, fmt

LOG = logging.getLogger(__name__)
ALLOWED_NAME = re.compile(r"^[^/\\.~][^/\\]*$")


def check_info(info):
    """ Validate info dict.
    """
    if not isinstance(info, dict):
        raise ValueError("bad metainfo - not a dictionary")

    pieces = info.get("pieces")
    if not isinstance(pieces, basestring) or len(pieces) % 20 != 0:
        raise ValueError("bad metainfo - bad pieces key")

    piece_size = info.get("piece length")
    if not isinstance(piece_size, (int, long)) or piece_size <= 0:
        raise ValueError("bad metainfo - illegal piece length")

    name = info.get("name")
    if not isinstance(name, basestring):
        raise ValueError("bad metainfo - bad name")
    if not ALLOWED_NAME.match(name):
        raise ValueError("name %s disallowed for security reasons" % name)

    if info.has_key("files") == info.has_key("length"):
        raise ValueError("single/multiple file mix")

    if info.has_key("length"):
        length = info.get("length")
        if not isinstance(length, (int, long)) or length < 0:
            raise ValueError("bad metainfo - bad length")
    else:
        files = info.get("files")
        if not isinstance(files, (list, tuple)):
            raise ValueError("bad metainfo - bad file list")

        for item in files:
            if not isinstance(item, dict):
                raise ValueError("bad metainfo - bad file value")

            length = item.get("length")
            if not isinstance(length, (int, long)) or length < 0:
                raise ValueError("bad metainfo - bad length")

            path = item.get("path")
            if not isinstance(path, (list, tuple)) or not path:
                raise ValueError("bad metainfo - bad path")

            for part in path:
                if not isinstance(part, basestring):
                    raise ValueError("bad metainfo - bad path dir")
                if not ALLOWED_NAME.match(part):
                    raise ValueError("path %s disallowed for security reasons" % part)

        file_paths = [os.sep.join(item["path"]) for item in files]
        if len(set(file_paths)) != len(file_paths):
            raise ValueError("bad metainfo - duplicate path")

    return info


def check_meta(meta):
    """ Validate meta dict.
    """
    if not isinstance(meta, dict):
        raise ValueError("bad metadata - not a dictionary")
    if not isinstance(meta.get("announce"), basestring):
        raise ValueError("bad announce URL - not a string")
    check_info(meta.get("info"))

    return meta


class Metafile(object):
    """ A torrent metafile.
    """

    # Patterns of names to ignore
    IGNORE_GLOB = [
        "core", "CVS", ".*", "*~", "*.swp", "*.tmp", "*.bak",
        "[Tt]humbs.db", "[Dd]esktop.ini", "ehthumbs_vista.db",
    ]


    def __init__(self, filename):
        """ Initialize metafile.
        """
        self.filename = filename
        self.progress = None
        self.datapath = None
        self.ignore = self.IGNORE_GLOB[:]


    def _scan(self):
        """ Generate paths in "self.datapath".
        """
        # Directory or single file?
        if os.path.isdir(self.datapath):
            # Walk the directory tree
            for dirpath, dirnames, filenames in os.walk(self.datapath):
                # Don't scan blacklisted directories
                for bad in dirnames[:]:
                    if any(fnmatch.fnmatch(bad, pattern) for pattern in self.ignore):
                        dirnames.remove(bad)

                # Yield all filenames that aren't blacklisted
                for filename in filenames:
                    if not any(fnmatch.fnmatch(filename, pattern) for pattern in self.ignore):
                        #yield os.path.join(dirpath[len(self.datapath)+1:], filename)
                        yield os.path.join(dirpath, filename)
        else:
            # Yield the filename
            yield self.datapath


    def _calc_size(self):
        """ Get total size of "self.datapath".
        """
        return sum(os.path.getsize(filename)
            for filename in self._scan()
        )


    def _make_info(self, piece_size, progress):
        """ Create info dict.
        """
        # These collect the file descriptions and piece hashes
        file_list = []
        pieces = []

        # Initialize progress state
        totalsize = self._calc_size()
        totalhashed = 0

        # Start a new piece
        sha1 = hashlib.sha1()
        done = 0
 
        # Hash all files
        for filename in sorted(self._scan()):
            # Assemble file info
            filesize = os.path.getsize(filename)
            file_list.append({
                "length": filesize, 
                "path": filename[len(self.datapath)+1:].replace(os.sep, '/').split('/'),
            })
            
            # Open file and hash it
            fileoffset = 0
            handle = open(filename, "rb")
            try:
                while fileoffset < filesize:
                    # Read rest of piece or file, whatever is smaller
                    chunk = handle.read(min(filesize - fileoffset, piece_size - done))
                    sha1.update(chunk)
                    done += len(chunk)
                    fileoffset += len(chunk)
                    totalhashed += len(chunk)
                    
                    # Piece is done
                    if done == piece_size:
                        pieces.append(sha1.digest())
                        
                        # Start a new piece
                        sha1 = hashlib.sha1()
                        done = 0

                    # Report progress
                    if progress:
                        progress(totalhashed, totalsize)
            finally:
                handle.close()

        # Add hash of partial last piece
        if done > 0:
            pieces.append(sha1.digest())

        # Build the meta dict
        metainfo = {
            "pieces": "".join(pieces),
            "piece length": piece_size, 
            "name": os.path.basename(self.datapath),
        }

        # Handle directory vs. single file        
        if os.path.isdir(self.datapath):
            metainfo["files"] = file_list
        else:
            metainfo["length"] = totalsize

        # Return validated info dict
        return check_info(metainfo)


    def _make_meta(self, tracker_url, root_name, private, progress):
        """ Create torrent dict.
        """
        # Calculate piece size
        datasize = self._calc_size()
        piece_size_exp = int(math.log(datasize) / math.log(2)) - 9
        piece_size_exp = min(max(15, piece_size_exp), 22)
        piece_size = 2 ** piece_size_exp

        # Build info hash
        info = self._make_info(piece_size, progress)

        # Enforce unique hash per tracker
        info["x_cross_seed"] = hashlib.md5(tracker_url).hexdigest()

        # Set private flag
        if private:
            info["private"] = 1

        # Freely chosen root name (default is basename of the data path)
        if root_name:
            info["name"] = root_name

        # Torrent metadata
        meta = {
            "info": info, 
            "announce": tracker_url.strip(), 
            "creation date": long(time.time())
        }

        #XXX meta["encoding"] = "UTF-8"

        # Return validated meta dict
        return check_meta(meta)


    def create(self, datapath, tracker_url, comment=None, root_name=None, created_by=None, private=False, progress=None):
        """ Create a metafile.
        """
        self.datapath = datapath.rstrip(os.sep)
        LOG.info("Creating %r for %r..." % (self.filename, self.datapath))

        meta = self._make_meta(tracker_url, root_name, private, progress)

        # Optional fields
        if comment:
            meta["comment"] = comment
        if created_by:
            meta["created by"] = created_by

        bencode.bwrite(self.filename, meta)
        return meta


    def listing(self):
        """ List torrent info & contents.
        """
        # Assemble data
        metainfo = bencode.bread(self.filename)
        announce = metainfo['announce']
        info = metainfo['info']
        info_hash = hashlib.sha1(bencode.bencode(info))

        if info.has_key('length'):
            # Single file
            total_size = info['length']
        else:
            # Directory structure
            total_size = sum([f['length'] for f in info['files']])

        piece_length = info['piece length']
        piece_number, last_piece_length = divmod(total_size, piece_length)

        # Build result
        result = [
            "NAME %s" % (os.path.basename(self.filename)),
            "SIZE %s (%i * %s + %s)" % (
                fmt.human_size(total_size).strip(),
                piece_number, fmt.human_size(piece_length).strip(),
                fmt.human_size(last_piece_length).strip(),
            ),
            "HASH %s" % (info_hash.hexdigest().upper()),
            "URL  %s" % announce,
            "PRV  %s" % ("YES (DHT/PEX disabled)" if info.get("private") else "NO (DHT/PEX enabled)"),
            "TIME %s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(metainfo["creation date"])),
        ]
        
        for label, key in (("BY  ", "created by"), ("REM ", "comment")):
            if key in metainfo:
                result.append("%s %s" % (label, metainfo[key]))
                
        result.extend([
            "",
            "FILE LISTING",
        ])
        if info.has_key('length'):
            # Single file
            result.append("%-69s%9s" % (
                    info['name'],
                    fmt.human_size(total_size),
            ))
        else:
            # Directory structure
            result.append("%s/" % info['name'])
            oldpaths = [None] * 99
            for entry in info['files']:
                for idx, item in enumerate(entry['path'][:-1]):
                    if item != oldpaths[idx]:
                        result.append("%s%s/" % (' ' * (4*(idx+1)), item))
                        oldpaths[idx] = item
                result.append("%-69s%9s" % (
                    ' ' * (4*len(entry['path'])) + entry['path'][-1],
                    fmt.human_size(entry['length']),
                ))

        return result

