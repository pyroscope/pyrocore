#! /usr/bin/env python-pyrocore
# -*- coding: utf-8 -*-
from __future__ import division, print_function

from collections import namedtuple

from pyrobase import fmt
from pyrocore import config
from pyrocore.scripts import base


def fmt_duration(secs):
    """Format a duration in seconds."""
    return ' '.join(fmt.human_duration(secs, 0, precision=2, short=True).strip().split())


class DownloadStats(base.ScriptBaseWithConfig):
    """
        Show stats about currently active downloads.
    """

    # argument description for the usage information
    ARGS_HELP = ""

    # set your own version
    VERSION = '1.0'

    STALLED_RATE = 5 * 1024
    FIELDS = ('is_active', 'left_bytes', 'down.rate')
    COMMANDS = tuple('d.{}='.format(x) for x in FIELDS)
    Download = namedtuple('Download', [x.replace('.', '_') for x in FIELDS])

    def add_options(self):
        """ Add program options.
        """
        super(DownloadStats, self).add_options()

    def mainloop(self):
        proxy = config.engine.open()
        items = proxy.d.multicall("incomplete", *self.COMMANDS)
        items = [self.Download(*x) for x in items]
        items = [d for d in items if d.is_active]

        total_left_bytes = sum(d.left_bytes for d in items)
        eta_min = min(d.left_bytes / d.down_rate for d in items if d.down_rate)
        eta_max = max(d.left_bytes / d.down_rate for d in items if d.down_rate)
        stalled = sum(d.down_rate < self.STALLED_RATE for d in items)
        down_rate = proxy.throttle.global_down.rate()

        print("Size left to download: ", fmt.human_size(total_left_bytes))
        print("Overall download speed:", fmt.human_size(down_rate) + '/s')
        print("ETA (min / max):       ",
            fmt_duration(eta_min), '…', fmt_duration(eta_max),
            '[{} item(s)'.format(len(items))
            + (', {} stalled'.format(stalled) if stalled else '') + ']',
        )


if __name__ == '__main__':
    base.ScriptBase.setup()
    DownloadStats().run()
