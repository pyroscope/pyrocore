#! /usr/bin/env python-pyrocore
# -*- coding: utf-8 -*-

from pyrocore import config
from pyrocore.scripts import base


class StuckTrackers(base.ScriptBaseWithConfig):
    """
        List started items whose announces are stuck, i.e. where
        last activity is older than the normal announce interval.
    """

    # argument description for the usage information
    ARGS_HELP = ""


    def add_options(self):
        """ Add program options.
        """
        super(StuckTrackers, self).add_options()

        # basic options
        self.add_bool_option("-a", "--all",
            help="list ALL items, not just stuck ones")


    def mainloop(self):
        import time
        from collections import namedtuple

        proxy = config.engine.open()
        now = int(time.time())
        fields = 'is_busy url min_interval normal_interval activity_time_last'.split()
        t_multicall = namedtuple('multicall', fields)
        rows = proxy.d.multicall('started', 't.multicall=,{}'.format(
            ','.join(['t.{}='.format(i) for i in fields])))

        print('{:>5s}  {:>5s}  {}'.format('#', 'Last', 'URL'))
        for idx, row in enumerate(rows, 1):
            t = t_multicall(*row[0][0])
            delta = now - t.activity_time_last
            if self.options.all or delta > t.normal_interval:
                print('{i:5d}  {m:>2d}:{s:02d}  {t.url}'
                      .format(t=t, i=idx, m=delta//60, s=delta%60))

        self.LOG.debug("XMLRPC stats: %s" % proxy)


if __name__ == "__main__":
    base.ScriptBase.setup()
    StuckTrackers().run()
