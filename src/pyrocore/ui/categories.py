# -*- coding: utf-8 -*-
# pylint: disable=
""" Category management.

    Copyright (c) 2017 The PyroScope Project <pyroscope.project@gmail.com>
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

from pyrocore import config, error
from pyrocore.util import xmlrpc
from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig


class CategoryManager(ScriptBaseWithConfig):
    """ Rotate through category views.
    """

    PREFIX = 'category_'
    PREFIX_LEN = len(PREFIX)

    # argument description for the usage information
    ARGS_HELP = ""


    def add_options(self):
        """ Add program options.
        """
        super(CategoryManager, self).add_options()

        self.add_bool_option("-l", "--list",
            help="list added category views")
        self.add_bool_option("-n", "--next",
            help="switch to next category view")
        self.add_bool_option("-p", "--prev",
            help="switch to previous category view")
        self.add_bool_option("-u", "--update",
            help="filter the current category view again")


    def mainloop(self):
        """ Manage category views.
        """
        # Get client state
        proxy = config.engine.open()
        views = [x for x in sorted(proxy.view.list()) if x.startswith(self.PREFIX)]

        current_view = real_current_view = proxy.ui.current_view()
        if current_view not in views:
            if views:
                current_view = views[0]
            else:
                raise error.UserError("There are no '{}*' views defined at all!".format(self.PREFIX))

        # Check options
        if self.options.list:
            for name in sorted(views):
                print("{} {:5d} {}".format(
                    '*' if name == real_current_view else ' ',
                    proxy.view.size(xmlrpc.NOHASH, name),
                    name[self.PREFIX_LEN:]))

        elif self.options.next or self.options.prev or self.options.update:
            # Determine next in line
            if self.options.update:
                new_view = current_view
            else:
                new_view = (views * 2)[views.index(current_view) + (1 if self.options.next else -1)]

            self.LOG.info("{} category view '{}'.".format(
                "Updating" if self.options.update else "Switching to", new_view))

            # Update and switch to filtered view
            proxy.pyro.category.update(xmlrpc.NOHASH, new_view[self.PREFIX_LEN:])
            proxy.ui.current_view.set(new_view)

        else:
            self.LOG.info("Current category view is '{}'.".format(current_view[self.PREFIX_LEN:]))
            self.LOG.info("Use '--help' to get usage information.")


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    CategoryManager().run()


if __name__ == "__main__":
    run()
