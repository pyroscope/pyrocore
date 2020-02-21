# -*- coding: utf-8 -*-
# pylint: disable=
""" rTorrent Daemon Jobs.

    Copyright (c) 2012 The PyroScope Project <pyroscope.project@gmail.com>
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

import requests
from requests.exceptions import RequestException, HTTPError

from pyrobase.parts import Bunch
from pyrocore import error
from pyrocore import config as config_ini
from pyrocore.util import fmt, xmlrpc, pymagic, stats


class EngineStats(object):
    """ rTorrent connection statistics logger.
    """

    def __init__(self, config=None):
        """ Set up statistics logger.
        """
        self.config = config or Bunch()
        self.LOG = pymagic.get_class_logger(self)
        self.LOG.debug("Statistics logger created with config %r" % self.config)


    def run(self):
        """ Statistics logger job callback.
        """
        try:
            proxy = config_ini.engine.open()
            self.LOG.info("Stats for %s - up %s, %s" % (
                config_ini.engine.engine_id,
                fmt.human_duration(proxy.system.time() - config_ini.engine.startup, 0, 2, True).strip(),
                proxy
            ))
        except (error.LoggableError, xmlrpc.ERRORS) as exc:
            self.LOG.warn(str(exc))


class InfluxDBStats(object):
    """ Push rTorrent and host statistics to InfluxDB.
    """

    def __init__(self, config=None):
        """ Set up InfluxDB logger.
        """
        self.config = config or Bunch()
        self.influxdb = Bunch(config_ini.influxdb)
        self.influxdb.timeout = float(self.influxdb.timeout or '0.250')

        self.LOG = pymagic.get_class_logger(self)
        if 'log_level' in self.config:
            self.LOG.setLevel(config.log_level)
        self.LOG.debug("InfluxDB statistics feed created with config %r" % self.config)


    def _influxdb_url(self):
        """ Return REST API URL to access time series.
        """
        url = "{0}/write?db={1}".format(self.influxdb.url.rstrip('/'), self.config.dbname)

        if self.influxdb.user and self.influxdb.password:
            url += "?u={0}&p={1}".format(self.influxdb.user, self.influxdb.password)

        return url

    def _influxdb_data(self):
        """ Return statitics data formatted according to InfluxDB's line protocol
        """
        datastr = ''

        try:
            proxy = config_ini.engine.open()
            hostname = proxy.system.hostname()
            pid = proxy.system.pid()
            data = stats.engine_data(config_ini.engine)
            views = data['views']
            del data['views']
            datastr = u"{0}stat,hostname={1},pid={2} ".format(
                self.config.series_prefix, hostname, pid)
            datastr += ','.join(['='.join([k, str(v)]) for k, v in data.items()]) + '\n'
            for view_name, values in views.items():
                vstr = u"{0}view,hostname={1},pid={2},name={3} ".format(
                    self.config.series_prefix, hostname, pid, view_name)
                vstr += ','.join(['='.join([k, str(v)]) for k, v in values.items()])
                datastr += vstr + "\n"
        except (error.LoggableError, xmlrpc.ERRORS) as exc:
            self.LOG.warn("InfluxDB stats: {0}".format(exc))
        return datastr

    def _push_data(self):
        """ Push stats data to InfluxDB.
        """
        # Assemble data
        datastr = self._influxdb_data()

        if not datastr:
            self.LOG.debug("InfluxDB stats: no data (previous errors?)")
            return

        # Encode into InfluxDB data packet
        fluxurl = self._influxdb_url()
        self.LOG.debug("POST to {0} with {1}".format(fluxurl.split('?')[0], datastr))

        # Push it!
        try:
            # TODO: Use a session
            r = requests.post(fluxurl, data=datastr, timeout=self.influxdb.timeout)
            r.raise_for_status()
        except RequestException as exc:
            self.LOG.warn("InfluxDB POST error: {0}".format(exc))
        except HTTPError as exc:
            self.LOG.warn("InfluxDB POST HTTP error {0}: Response: {1}".format(
                str(r.status_code), r.content))


    def run(self):
        """ Statistics feed job callback.
        """
        self._push_data()


def module_test():
    """ Quick test using…

            python -m pyrocore.torrent.jobs
    """
    import pprint
    from pyrocore import connect

    try:
        engine = connect()
        print("%s - %s" % (engine.engine_id, engine.open()))

        data, views = _flux_engine_data(engine)
        print "data = ",
        pprint.pprint(data)
        print "views = ",
        pprint.pprint(views)

        print("%s - %s" % (engine.engine_id, engine.open()))
    except (error.LoggableError, xmlrpc.ERRORS) as torrent_exc:
        print("ERROR: %s" % torrent_exc)


if __name__ == "__main__":
    module_test()
