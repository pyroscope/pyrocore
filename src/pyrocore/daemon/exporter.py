import threading
from time import sleep
from collections import Counter

from pyrocore import config as config_ini
from pyrocore.util import pymagic
from pyrobase.parts import Bunch

from prometheus_client import start_http_server, Gauge
from prometheus_client.core import GaugeMetricFamily, REGISTRY

class ClientServer(threading.Thread):
    def __init__(self, port):
        super(ClientServer, self).__init__()
        self.port = int(port)

    def run(self):
        start_http_server(self.port)

class RtorrentCollector(object):
    def __init__(self, proxy, config):
        self.proxy = proxy
        self.config = config
        self.prefix = self.config.get('prefix', 'rtorrent_')


    def collect(self):
        raise NotImplementedError

class RtorrentItemCollector(RtorrentCollector):
    def __init__(self, proxy, config):
        super(RtorrentItemCollector, self).__init__(proxy, config)

        available_methods = set(self.proxy.system.listMethods())
        if 'item-stats' in self.config:
            self.item_stat_methods = set(self.config['item-stats'].split(',')) & available_methods
        else:
            self.item_stat_methods = ("down.total", "up.total")
        if 'item-labels' in self.config:
            self.item_labels = list(set(self.config['item-labels'].split(',')) & available_methods)
        else:
            self.item_labels = ["hash", "name"]


    def collect(self):
        calls = ["d."+m+"=" for m in list(self.item_stat_methods) + self.item_labels]
        result = self.proxy.d.multicall("main", *calls)
        item_stats = {}
        for stat in self.item_stat_methods:
            item_stats[stat] = GaugeMetricFamily(self.prefix + stat.replace('.', '_'), stat, labels=self.item_labels)
        for i in result:
            info = dict(list(zip(list(self.item_stat_methods) + self.item_labels, i)))
            for stat, gauge in item_stats.items():
                gauge.add_metric([info[l] for l in self.item_labels], info[stat])
        for stat, guage in item_stats.items():
            yield guage


class RtorrentTrackerCollector(RtorrentCollector):
    def __init__(self, proxy, config):
        super(RtorrentTrackerCollector, self).__init__(proxy, config)

    def collect(self):
        tracker_gauge = GaugeMetricFamily(self.prefix + 'tracker_amount',
                                          'Number of torrents belonging to a specific tracker', labels=['alias'])
        tracker_error_gauge = GaugeMetricFamily(self.prefix + 'tracker_errors',
                                                'Number of torrents with tracker errors belonging to a specific tracker', labels=['alias'])

        item_fields = ["d.tracker_domain=", "d.message="]
        result = self.proxy.d.multicall("main", *item_fields)

        trackers = Counter([config_ini.map_announce2alias(d[0]) for d in result])
        tracker_errors = Counter([config_ini.map_announce2alias(d[0]) for d in result if d[1]])

        for k, v in trackers.items():
            tracker_gauge.add_metric([k], v)
        for k in trackers.keys(): # Use the tracker keys to make sure all active trackers get a value
            tracker_error_gauge.add_metric([k], tracker_errors[k])

        yield tracker_gauge
        yield tracker_error_gauge

class RtorrentSystemCollector(RtorrentCollector):
    def __init__(self, proxy, config):
        super(RtorrentSystemCollector, self).__init__(proxy, config)
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

        self.info_methods = ['system.client_version', 'system.library_version']

        # Strip out unavailable methods
        self.system_stats = set(stat_methods) & set(self.proxy.system.listMethods())

    def collect(self):
        system_info = GaugeMetricFamily(self.prefix + "info", "rTorrent platform information", labels=[m.replace('.','_') for m in self.info_methods])
        system_view_size = GaugeMetricFamily(self.prefix + "view_size", "Size of rtorrent views", labels=["view"])
        views = self.proxy.view.list()

        # Get data via multicall
        calls = [dict(methodName=method, params=[]) for method in sorted(self.system_stats)] \
                + [dict(methodName=method, params=[]) for method in self.info_methods] \
                + [dict(methodName="view.size", params=['', view]) for view in views]

        result = self.proxy.system.multicall(calls, flatten=True)

        # Get numeric metrics
        for m in sorted(self.system_stats):
            yield GaugeMetricFamily(self.prefix + m.replace('.', '_'), m, value=result[0])
            del result[0]

        # Get text-like information
        system_info.add_metric(result[0:len(result)-len(views)], 1)
        yield system_info
        result = result[-len(views):]

        # Get view information
        for v in views:
            system_view_size.add_metric([v], result[0])
            del result[0]
        yield system_view_size

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
        self.system_stats_initialized = False
        jobs = {
            "item": RtorrentItemCollector,
            "tracker": RtorrentTrackerCollector,
            "system": RtorrentSystemCollector
        }
        for j in self.config.get('jobs', 'system').split(','):
             j = j.strip()
             if j not in jobs:
                 self.LOG.error("Job {} not found, skipping".format(j))
             else:
                 REGISTRY.register(jobs[j](self.proxy, self.config))

        # Start the server right off the bat
        self.prom_thread = ClientServer(self.config.get('port', '8000'))
        self.prom_thread.start()


    def run(self):
        # NOOP, stats are generated at scrape time
        pass

if __name__ == '__main__':
    from pyrocore import connect
    engine = connect()

    i = RtorrentExporter(Bunch(jobs="system,tracker,item", port=8005))
    i.proxy = engine.open()
    while True:
        i.run()
        sleep(5)
