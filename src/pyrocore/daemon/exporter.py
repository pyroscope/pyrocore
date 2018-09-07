import threading
from time import sleep
from collections import Counter

from pyrocore import config as config_ini
from pyrocore.util import pymagic
from pyrobase.parts import Bunch

from prometheus_client import start_http_server, Gauge

class ClientServer(threading.Thread):
    def __init__(self, port):
        super(ClientServer, self).__init__()
        self.port = int(port)

    def run(self):
        start_http_server(self.port)

class RtorrentExporter(object):
    """ Expose rTorrent and host statistics for scraping by a Prometheus instance.
    """

    def __init__(self, config=None):
        """ Set up RtorrentExporter.
        """
        self.config = config or Bunch()
        self.LOG = pymagic.get_class_logger(self)
        if 'log_level' in self.config:
            self.LOG.setLevel(config.log_level)
        self.LOG.debug("RtorrentExporter created with config %r" % self.config)
        self.prefix = self.config.get('prefix', 'rtorrent_')
        self.proxy = config_ini.engine.open()
        self.jobs = []
        jobs_init = {
            'tracker': self._init_tracker_stats,
            'system': self._init_system_stats,
            'item': self._init_item_stats
        }
        for j in self.config.get('jobs', 'system').split(','):
            if j in ['tracker', 'system', 'item']:
                self.jobs.append(j)
                jobs_init[j]()
            else:
                self.LOG.error("Unknown job '{}' requested, not initializing it".format(j))
        if not self.jobs:
            raise RuntimeError("Job configuration '{}' contained no valid jobs".format(self.config.get('jobs')))
        # Start the server right off the bat
        self.prom_thread = ClientServer(self.config.get('port', '8000'))
        self.prom_thread.start()


    def run(self):
        """Update any defined metrics
        """
        # Update requested stats
        jobs = {
            'tracker': self._fetch_tracker_stats,
            'system': self._fetch_system_stats,
            'item': self._fetch_item_stats
        }
        for j in self.jobs:
            jobs[j]()

    def _init_item_stats(self):
        available_methods = set(self.proxy.system.listMethods())
        if 'item_stats' in self.config:
            item_stat_methods = self.config['item_stats'].split(',')
            item_stat_methods = set(item_stat_methods) & available_methods
        else:
            item_stat_methods = ("down.total", "up.total")
        if 'item_labels' in self.config:
            item_labels = self.config['item_labels'].split(',')
            self.item_labels = list(set(item_labels) & available_methods)
        else:
            self.item_labels = ["hash", "name"]
        self.item_stats = {}
        for m in item_stat_methods:
            self.item_stats[m] = Gauge(self.prefix + "item_" + m.replace('.', '_'), m, self.item_labels)

    def _fetch_item_stats(self):
        """Use d.multicall2 to
        """
        calls = ["d."+m+"=" for m in list(self.item_stats.keys()) + self.item_labels]
        result = self.proxy.d.multicall2('', "main", *calls)
        for i in result:
            info = dict(list(zip(list(self.item_stats.keys()) + self.item_labels, i)))
            for stat, gauge in self.item_stats.items():
                gauge.labels(*[info[l] for l in self.item_labels]).set(info[stat])

    def _init_tracker_stats(self):
        """Initialize the tracker gauges
        """
        self.tracker_gauge = Gauge(self.prefix + 'tracker_amount', 'Number of torrents belonging to a specific tracker', ['alias'])
        self.tracker_error_gauge = Gauge(self.prefix + 'tracker_errors',
                                         'Number of torrents with tracker errors belonging to a specific tracker', ['alias'])


    def _fetch_tracker_stats(self):
        """Scrape tracker metrics from item information
        """
        item_fields = ["d.tracker_domain=", "d.message="]

        result = self.proxy.d.multicall("main", *item_fields)

        trackers = Counter([config_ini.map_announce2alias(d[0]) for d in result])
        tracker_errors = Counter([config_ini.map_announce2alias(d[0]) for d in result if d[1]])

        for k, v in trackers.items():
            self.tracker_gauge.labels(k).set(v)
        for k in trackers.keys(): # Use the tracker keys to make sure all active trackers get a value
            self.tracker_error_gauge.labels(k).set(tracker_errors[k])

    def _init_system_stats(self):
        """Initialize the system gauges
        """
        stat_methods = [
            "throttle.global_up.rate", "throttle.global_up.max_rate", "throttle.global_up.total",
            "throttle.global_down.rate", "throttle.global_down.max_rate", "throttle.global_down.total",
            "pieces.stats_not_preloaded", "pieces.stats_preloaded",
            "system.files.opened_counter", "system.files.failed_counter", "system.files.closed_counter",
            "pieces.memory.block_count", "pieces.memory.current", "pieces.memory.max",
            "network.open_sockets", "pieces.sync.queue_size",
            "pieces.stats.total_size", "pieces.preload.type",
            "pieces.preload.min_size", "pieces.preload.min_rate",
            "pieces.memory.sync_queue", "network.max_open_files",
            "network.max_open_sockets", "network.http.max_open",
            "throttle.max_downloads.global", "throttle.max_uploads.global",
            "startup_time", "network.http.current_open"
        ]

        info_methods = ['system.client_version', 'system.library_version']

        self.system_stats = {}
        for m in set(stat_methods) & set(self.proxy.system.listMethods()): # Strip out any methods that aren't available on the system
            self.system_stats[m] = Gauge(self.prefix + m.replace('.', '_'), m)
        self.system_info = Gauge(self.prefix + "info", "rTorrent platform information", [m.replace('.','_') for m in info_methods])
        self.system_view_size = Gauge(self.prefix + "view_size", "Size of rtorrent views", ["view"])

    def _fetch_system_stats(self):
        """Scrape system and view statistics
        """
        info_methods = ['system.client_version', 'system.library_version']
        views = self.proxy.view.list()

        # Get data via multicall
        # Sort the system stats because we can't trust py2 keys() to be deterministic
        calls = [dict(methodName=method, params=[]) for method in sorted(self.system_stats.keys())] \
                + [dict(methodName=method, params=[]) for method in info_methods] \
                + [dict(methodName="view.size", params=['', view]) for view in views]

        result = self.proxy.system.multicall(calls, flatten=True)

        # Get numeric metrics
        for m in sorted(self.system_stats.keys()):
            self.system_stats[m].set(result[0])
            del result[0]

        # Get text-like information
        info_methods = [m.replace('.', '_') for m in info_methods]
        self.system_info.labels(*result[0:len(result)-len(views)]).set(1)
        result = result[-len(views):]

        # Get view information
        for v in views:
            self.system_view_size.labels(v).set(result[0])
            del result[0]


def module_test():
    from pyrocore import connect
    engine = connect()

    i = RtorrentExporter(Bunch(jobs="system,tracker,item",port="8100"))
    i.proxy = engine.open()
    while True:
        i.run()
        sleep(5)

if __name__ == '__main__':
    module_test()
