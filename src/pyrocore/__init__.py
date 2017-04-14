# -*- coding: utf-8 -*-
# pylint: disable=
""" Python Torrent Tools Core Package.

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


def connect(config_dir=None, optional_config_files=None, cron_cfg="cron"):
    """ Initialize everything for interactive use.

        Returns a ready-to-use RtorrentEngine object.
    """
    from pyrocore.scripts.base import ScriptBase
    from pyrocore.util import load_config

    ScriptBase.setup(cron_cfg=cron_cfg)
    load_config.ConfigLoader(config_dir).load(optional_config_files or [])

    from pyrocore import config
    config.engine.open()
    return config.engine
