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

try:
    import json
except ImportError:
    import simplejson as json # pylint: disable=F0401

import requests
from requests.exceptions import RequestException

from pyrobase.parts import Bunch
from pyrocore import error
from pyrocore import config as config_ini
from pyrocore.util import fmt, xmlrpc, pymagic, stats


def _flux_engine_data(engine):
    """ Return rTorrent data set for pushing to InfluxDB.
    """
    data = stats.engine_data(engine)

    # Make it flat
    data["up_rate"] = data["upload"][0]
    data["up_limit"] = data["upload"][1]
    data["down_rate"] = data["download"][0]
    data["down_limit"] = data["download"][1]
    data["version"] = data["versions"][0]
    views = data["views"]

    del data["upload"]
    del data["download"]
    del data["versions"]
    del data["views"]

    return data, views


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
        except (error.LoggableError, xmlrpc.ERRORS), exc:
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
        self.LOG.debug("InfluxDB statistics feed created with config %r" % self.config)


    def _influxdb_url(self):
        """ Return REST API URL to access time series.
        """
        url = "{0}/db/{1}/series".format(self.influxdb.url.rstrip('/'), self.config.dbname)

        if self.influxdb.user and self.influxdb.password:
            url += "?u={0}&p={1}".format(self.influxdb.user, self.influxdb.password)

        return url


    def _push_data(self):
        """ Push stats data to InfluxDB.
        """
        if not (self.config.series or self.config.series_host):
            self.LOG.info("Misconfigured InfluxDB job, neither 'series' nor 'series_host' is set!")
            return

        # Assemble data
        fluxdata = []

        if self.config.series:
            try:
                config_ini.engine.open()
                data, views = _flux_engine_data(config_ini.engine)
                fluxdata.append(dict(
                    name=self.config.series,
                    columns=data.keys(),
                    points=[data.values()]
                ))
                fluxdata.append(dict(
                    name=self.config.series + '_views',
                    columns=views.keys(),
                    points=[views.values()]
                ))
            except (error.LoggableError, xmlrpc.ERRORS), exc:
                self.LOG.warn("InfluxDB stats: {0}".format(exc))

#        if self.config.series_host:
#            fluxdata.append(dict(
#                name = self.config.series_host,
#                columns = .keys(),
#                points = [.values()]
#            ))

        if not fluxdata:
            self.LOG.debug("InfluxDB stats: no data (previous errors?)")
            return

        # Encode into InfluxDB data packet
        fluxurl = self._influxdb_url()
        fluxjson = json.dumps(fluxdata)
        self.LOG.debug("POST to {0} with {1}".format(fluxurl.split('?')[0], fluxjson))

        # Push it!
        try:
            # TODO: Use a session
            requests.post(fluxurl, data=fluxjson, timeout=self.influxdb.timeout)
        except RequestException, exc:
            self.LOG.info("InfluxDB POST error: {0}".format(exc))


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
    except (error.LoggableError, xmlrpc.ERRORS), torrent_exc:
        print("ERROR: %s" % torrent_exc)


if __name__ == "__main__":
    module_test()
