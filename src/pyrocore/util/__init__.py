# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
""" Utility Modules.

    Copyright (c) 2010 The PyroScope Project <pyroscope.project@gmail.com>
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

import os

# 0.4.1 refactoring, duplicate stuf into the old place
from pyrobase import fmt


if not os.path.supports_unicode_filenames:
    # Make a Unicode-aware copy of os and os.path
    from pyrobase.parts import Bunch

    def _encode_path(text):
        """ Return a string suitable for calling file system functions.
        """
        if isinstance(text, str):
            return text
        else:
            return text.encode("UTF-8")

    # copy "os" identifiers
    _os = Bunch()
    for _key in os.__all__:
        _os[_key] = getattr(os, _key)

    def _wrap(name, func):
        "Wrapping helper."
        setattr(_os, name, func)
        func.__name__ = name
        func.__doc__ = getattr(os, name).__doc__

    # wrap some os functions
    _wrap("makedirs", lambda path, o=os: o.makedirs(_encode_path(path)))
    _wrap("readlink", lambda path, o=os: o.readlink(_encode_path(path)))
    _wrap("remove", lambda path, o=os: o.remove(_encode_path(path)))
    _wrap("rename", lambda src, dst, o=os: o.rename(_encode_path(src), _encode_path(dst)))
    _wrap("symlink", lambda src, dst, o=os: o.symlink(_encode_path(src), _encode_path(dst)))
    _wrap("listdir", lambda path, o=os: o.listdir(_encode_path(path)))
    _wrap("rmdir", lambda path, o=os: o.rmdir(_encode_path(path)))
    _wrap("removedirs", lambda path, o=os: o.removedirs(_encode_path(path)))

    # wrap os.path stuff
    _unary_fs_functions = [
        'getsize', 'getmtime', 'getatime', 'getctime', 'islink', 'exists', 'lexists',
        'isdir', 'isfile', 'ismount', 'abspath', 'realpath'
        #'samefile', 'sameopenfile', 'samestat', , 'supports_unicode_filenames'
    ]
    _os_path = Bunch()
    for _key in os.path.__all__:
        _os_path[_key] = getattr(os.path, _key)
        if _key in _unary_fs_functions:
            _os_path[_key] = lambda x, _f=_os_path[_key]: _f(_encode_path(x))

    os = _os
    os.path = _os_path
    del Bunch, _unary_fs_functions, _key, _wrap, _os, _os_path
