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
        self.add_bool_option("-s", "--stuck-only",
            help="list just stuck items / skip 'no enabled trackers' check")
        self.add_bool_option("-t", "--to-tagged",
            help="add stuck items to 'tagged' view")


    def mainloop(self):
        import time
        from urlparse import urlparse
        from collections import namedtuple, Counter

        from pyrobase import fmt
        from pyrocore.util import xmlrpc

        proxy = config.engine.open()
        now = int(time.time())
        fields = ('is_enabled is_busy url min_interval normal_interval'
                  ' activity_time_last success_counter failed_counter scrape_counter').split()
        t_multicall = namedtuple('multicall', fields)
        rows = proxy.d.multicall('started', 'd.hash=', 't.multicall=,{}'.format(
            ','.join(['t.{}='.format(i) for i in fields])))
        stuck = Counter()

        view = 'tagged'
        if self.options.to_tagged and view not in proxy.view.list():
            proxy.view.add(xmlrpc.NOHASH, view)

        print('{:>5s}  {:>2s}  {:>5s}  {:>5s} {:>6s}  {:>13s}  {:40s}  {}'
              .format('S#', 'T#', 'OK', 'Error', 'Scrape', 'Last Announce',
                      'Infohash', 'Tracker Domain'))
        for idx, (infohash, trackers) in enumerate(rows, 1):
            trackers = [t_multicall(*t) for t in trackers]

            if not any(t.is_enabled for t in trackers):
                if self.options.stuck_only:
                    continue
                if self.options.to_tagged:
                    proxy.view.set_visible(infohash, view)
                domain = 'ALL TRACKERS DISABLED' if trackers else 'NO TRACKERS'
                stuck[domain] += 1
                print('{i:5d}  {n:>2s}  {n:>5s}  {n:>5s}  {n:>5s}  {delta:>13s}  {hash}  {domain}'
                      .format(i=idx, n='-', hash=infohash, delta='N/A', domain=domain))
                continue

            for num, t in enumerate(trackers, 1):
                if not t.is_enabled:
                    continue

                delta = now - t.activity_time_last
                if self.options.all or delta > t.normal_interval:
                    if self.options.to_tagged:
                        proxy.view.set_visible(infohash, view)
                    domain = urlparse(t.url).netloc.split(':')[0]
                    stuck[domain] += 1

                    print('{i:5d}  {n:2d}  '
                          '{t.success_counter:5d}  {t.scrape_counter:5d}  {t.failed_counter:5d}  '
                          '{delta}  {hash}  {domain}'
                          .format(t=t, i=idx, n=num, hash=infohash, domain=domain,
                                  delta=fmt.human_duration(t.activity_time_last,
                                                           precision=2, short=True)))

        if sum(stuck.values()):
            if self.options.to_tagged:
                proxy.ui.current_view.set(view)
            self.LOG.info("Stuck items: TOTAL={}, {}".format(sum(stuck.values()),
                ', '.join(['{}={}'.format(*i) for i in stuck.most_common()])))
        self.LOG.debug("XMLRPC stats: %s" % proxy)


if __name__ == "__main__":
    base.ScriptBase.setup()
    StuckTrackers().run()
