# -*- coding: utf-8 -*-
# pylint: disable=I0011,C0103
""" rTorrent Disk Space House-Keeping.

    This is used in the ``rtsweep`` tool and the queue job of the
    ``pyrotoque`` daemon to free up disk space for new items, by
    deleting old items in a controlled way using a configurable order.

    Copyright (c) 2018 The PyroScope Project <pyroscope.project@gmail.com>
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

from collections import namedtuple

from pyrocore import error
from pyrocore import config as config_ini
from pyrocore.torrent import engine, matching


SweepRule = namedtuple('SweepRule', 'ruleset name prio order filter')


def parse_cond(text):
    """Parse a filter condition."""
    return matching.ConditionParser(engine.FieldDefinition.lookup, "name").parse(text)


class DiskSpaceManager(object):
    """Core implementation of ``rtsweep``."""

    def __init__(self, config=None, rulesets=None):
        self.config = config or config_ini
        self.active_rulesets = rulesets or [x.strip() for x in self.config.sweep['default_rules'].split(',')]
        self.rules = []
        self.default_order = self.config.sweep['default_order']
        self.protected = parse_cond(self.config.sweep['filter_protected'])

        self._load_rules()

    def _load_rules(self):
        """Load rule definitions from config."""
        for ruleset in self.active_rulesets:
            section_name = 'sweep_rules_' + ruleset.lower()
            try:
                ruledefs = getattr(self.config, section_name)
            except AttributeError:
                raise error.UserError("There is no [{}] section in your configuration"
                                      .format(section_name.upper()))
            for ruledef, filtercond in ruledefs.items():
                if ruledef.endswith('.filter'):
                    rulename = ruledef.rsplit('.', 1)[0]
                    rule = SweepRule(ruleset, rulename,
                                     int(ruledefs.get(rulename + '.prio', '999')),
                                     ruledefs.get(rulename + '.order', self.default_order),
                                     parse_cond(filtercond))
                    self.rules.append(rule)

        self.rules.sort(key=lambda x: (x.prio, x.name))

        return self.rules

#    test "$1" = "--aggressive" && { shift; activity=5i; } || activity=4h
#        $DRY ~/bin/rtcontrol -/1 --cull active=+$activity [ NOT [ $PROTECTED ] ] \
#            -qco loaded,size.sz,uploaded.sz,seedtime,ratio,name "$@" $INTERACTIVE; rc=$?
#   log.debug("No matches for {ruleset}

##needed=$(( $requested + $RESERVED_GiB * $GiB )) # Add a few GiB for the system
##log.info"Disk space management started [with $(print_gib $(download_free)) free]")

# Finally, go through everything sorted by age (with staged activity protection)
## -s loaded //
## --aggressive -s loaded //

#    $INFO "Disk space management finished in ${took_secs}s [$(print_gib $(download_free)) free," \
#        "$(print_gib $requested) requested]"
#        $INFO "Removed $(( $start_items - $after_items )) item(s)," \
#            "freeing $(print_gib $(( $after_free - $start_free ))) disk space" \
#            "[now $(print_gib $(download_free)) free, took ${took_secs}s]."
