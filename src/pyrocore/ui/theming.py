# -*- coding: utf-8 -*-
# pylint: disable=
""" Color theme support.

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

import sys
import glob

from pyrocore.scripts.base import ScriptBase, ScriptBaseWithConfig
from pyrocore.util import os


class ThemeSwitcher(ScriptBaseWithConfig):
    """ Rotate through color themes.
    """

    # argument description for the usage information
    ARGS_HELP = ""


    def add_options(self):
        """ Add program options.
        """
        super(ThemeSwitcher, self).add_options()

        self.add_bool_option("-l", "--list",
            help="list available themes")
        self.add_bool_option("-c", "--current",
            help="print path to currently selected theme")
        self.add_bool_option("-n", "--next",
            help="rotate through selected themes, and print new path")
        self.add_bool_option("-a", "--all",
            help="remove any selections, and use all themes")
        self.add_value_option("-t", "--toggle", "NAME",
            help="toggle selection of a theme")


    def mainloop(self):
        """ Handle theme selection changes, or rotate through selection.
        """
        config_dir = self.options.config_dir or os.path.expanduser("~/.pyroscope")
        themes_dir = os.path.join(config_dir, 'color-schemes')
        selected_file = os.path.join(themes_dir, '.selected')
        current_file = os.path.join(themes_dir, '.current')

        # Read persisted state
        selected_themes = []
        if os.path.exists(selected_file):
            with open(selected_file, 'rt') as handle:
                selected_themes = [x.strip() for x in handle]

        current_theme = None
        if os.path.exists(current_file):
            with open(current_file, 'rt') as handle:
                current_theme = handle.readline().strip()

        # Scan config for available themes
        themes = {}
        for ext in ('.rc.default', '.rc'):
            for filepath in glob.glob(themes_dir + '/*' + ext):
                name = os.path.basename(filepath).split('.')[0]
                if name:
                    themes.setdefault(name, filepath)

        # Use available selected themes in given order, if there are any, else all themes
        if selected_themes and not set(selected_themes).isdisjoint(set(themes)):
            theme_list = [x for x in selected_themes if x in themes]
        else:
            theme_list = list(sorted(themes))

        # Check options
        if self.options.list or self.options.all or self.options.toggle:
            if self.options.all:
                if os.path.exists(selected_file):
                    os.remove(selected_file)
                selected_themes = []

            for name in (self.options.toggle or '').replace(',', ' ').split():
                if name not in themes:
                    self.parser.error("Unknown theme {0!r}, use '--list' to show them".format(name))
                elif name in selected_themes:
                    selected_themes = [x for x in selected_themes if x != name]
                else:
                    selected_themes.append(name)

                with open(selected_file, 'wt') as handle:
                    handle.write('\n'.join(selected_themes + ['']))

            if self.options.list:
                for name in sorted(themes):
                    print("{} {} {}".format(
                        '*' if name == current_theme else ' ',
                        '{:2d}'.format(selected_themes.index(name) + 1)
                            if name in selected_themes else '  ',
                        name,
                    ))

        elif self.options.current or self.options.next:
            # Determine current theme, or rotate to next one
            new_theme = theme_list[0]
            if self.options.current and current_theme in theme_list:
                new_theme = current_theme
            elif current_theme in theme_list:
                new_theme = (theme_list * 2)[theme_list.index(current_theme) + 1]

            # Persist new theme
            if new_theme != current_theme:
                with open(current_file, 'wt') as handle:
                    handle.write(new_theme + '\n')

            # Return result
            sys.stdout.write(themes[new_theme])
            sys.stdout.flush()

        else:
            self.LOG.info("Current color theme is '{}'.".format(
                current_theme if current_theme in theme_list else theme_list[0]))
            self.LOG.info("Use '--help' to get usage information.")


def run(): #pragma: no cover
    """ The entry point.
    """
    ScriptBase.setup()
    ThemeSwitcher().run()


if __name__ == "__main__":
    run()
