""" FlexGet Plugins Package.

    To load all PyroScope plugins into FlexGet, create the file 
    "~/.flexget/plugins/pyroflex.py" with this content::
        from pyrocore.flexget import *

    That's all. Check with "flexget --plugins | grep pyro_".

    Copyright (c) 2011 The PyroScope Project <pyroscope.project@gmail.com>
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
import os
import pkg_resources

from flexget import plugin

from pyrocore.util import pymagic


def load_plugin_classes():
    """ From all modules in this package, load a dict of the plugin classes.
    """
    plugins = {}
    modules = set(os.path.splitext(module_file)[0]
        for module_file in pkg_resources.resource_listdir(__name__, '') #@UndefinedVariable
        if not module_file.startswith('_') and module_file.endswith(".py")
    )
    
    for module in modules:
        for name, obj in vars(pymagic.import_name(__name__, module)).items():
            if isinstance(obj, type) and issubclass(obj, plugin.Plugin) and not name.endswith("PluginBase"):
                plugins[name] = obj

    return plugins


FLEXGET_BOOTSTRAP = "~/.flexget/plugins/pyroflex.py"
PLUGINS = load_plugin_classes()
globals().update(PLUGINS)
__all__ = list(PLUGINS.keys()) + ["PLUGINS", "FLEXGET_BOOTSTRAP"]
