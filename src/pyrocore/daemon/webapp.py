# -*- coding: utf-8 -*-
# pylint: disable=I0011
""" rTorrent web apps.

    Copyright (c) 2013 The PyroScope Project <pyroscope.project@gmail.com>
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
import os
import re
import json
import time
import socket
import logging
import mimetypes

import psutil

from webob import exc, static, Request, Response
from webob.dec import wsgify
#from webob.response import Response

from pyrobase.parts import Bunch
from pyrocore import config, error
from pyrocore.util import pymagic, xmlrpc


def engine_data(engine):
    """ Get important performance data and metadata from rTorrent.
    """
    views = ("main", "started", "stopped", "complete", "incomplete", "seeding", "leeching", "active", "messages")
    methods = [
        "get_up_rate", "get_upload_rate",
        "get_down_rate", "get_download_rate",
    ]

    # Get data via multicall
    proxy = engine.open()
    calls = [dict(methodName=method, params=[]) for method in methods] \
          + [dict(methodName="view.size", params=['', view]) for view in views]
    result = proxy.system.multicall(calls, flatten=True)

    # Build result object
    data = dict(
        now         = time.time(),
        engine_id   = engine.engine_id,
        versions    = engine.versions,
        uptime      = engine.uptime,
        upload      = [result[0], result[1]],
        download    = [result[2], result[3]],
        views       = dict([(name, result[4+i])
            for i, name in enumerate(views)
        ]),
    )

    return data


class StaticFolders(object):
    """ An application that serves up the files in a list of given directories.

        Non-existent paths are ignored.
        Pass a `fileapp` factory to change the default file serving app.
    """

    def __init__(self, paths, fileapp=None, **kw):
        self.LOG = pymagic.get_class_logger(self)
        self.paths = []
        self.fileapp = fileapp or static.FileApp
        self.fileapp_kw = kw
        
        for path in paths:
            path = os.path.abspath(path).rstrip(os.path.sep) + os.path.sep
            if os.path.isdir(path):
                self.paths.append(path)
            else:
                self.LOG.warn("Static HTTP directory %r not found, ignoring it" % path)


    @wsgify
    def __call__(self, req):
        urlpath = req.urlvars.filepath.strip('/').replace("..", "!FORBIDDEN!")
    
        for basepath in self.paths:
            path = os.path.abspath(os.path.realpath(os.path.join(basepath, urlpath)))
            if not os.path.isfile(path):
                continue
            elif not path.startswith(basepath):
                return exc.HTTPForbidden(comment="Won't follow symlink to %r" % urlpath)
            else:
                return self.fileapp(path, **self.fileapp_kw)

        return exc.HTTPNotFound(comment=urlpath)


class JsonController(object):
    """ Controller for generating JSON data.
    """

    ERRORS_LOGGED = set()

    
    def __init__(self, **kwargs):
        self.LOG = pymagic.get_class_logger(self)
        self.cfg = Bunch(kwargs)


    @wsgify
    def __call__(self, req):
        action = req.urlvars.get("action")
        try:
            try:
                method = getattr(self, "json_" + action)
            except AttributeError:
                raise exc.HTTPNotFound("No action '%s'" % action)

            resp = method(req)

            if isinstance(resp, (dict, list)):
                try:
                    resp = json.dumps(resp, sort_keys=True)
                except (TypeError, ValueError, IndexError, AttributeError), json_exc:
                    raise exc.HTTPInternalServerError("JSON serialization error (%s)" % json_exc)
            if isinstance(resp, basestring):
                resp = Response(body=resp, content_type="application/json")
        except exc.HTTPException, http_exc:
            resp = http_exc
        return resp


    def guarded(self, func, *args, **kwargs):
        """ Call a function, return None on errors.
        """
        try:
            return func(*args, **kwargs)
        except (EnvironmentError, error.LoggableError, xmlrpc.ERRORS), g_exc:
            if func.__name__ not in self.ERRORS_LOGGED:
                self.LOG.warn("While calling '%s': %s" % (func.__name__, g_exc))
                self.ERRORS_LOGGED.add(func.__name__)
            return None    


    def json_engine(self, req):
        """ Return torrent engine data.
        """
        try:
            return engine_data(config.engine)
        except (error.LoggableError, xmlrpc.ERRORS), torrent_exc:
            raise exc.HTTPInternalServerError(str(torrent_exc))


    def json_charts(self, req):
        """ Return charting data.
        """
        disk_used, disk_total = 0, 0
        for disk_usage_path in self.cfg.disk_usage_path.split(os.pathsep):
            disk_usage = self.guarded(psutil.disk_usage, os.path.expanduser(disk_usage_path.strip()))
            if disk_usage:
                disk_used += disk_usage.used
                disk_total += disk_usage.total

        data = dict(
            engine      = self.json_engine(req),
            uptime      = time.time() - psutil.BOOT_TIME,
            fqdn        = self.guarded(socket.getfqdn),
            cpu_usage   = self.guarded(psutil.cpu_percent, 0),
            ram_usage   = self.guarded(psutil.virtual_memory),
            swap_usage  = self.guarded(psutil.swap_memory),
            disk_usage  = (disk_used, disk_total) if disk_total else None,
            disk_io     = self.guarded(psutil.disk_io_counters),
            net_io      = self.guarded(psutil.network_io_counters),
        )
        return data


class Router(object):
    """ URL router middleware.
    
        See http://docs.webob.org/en/latest/do-it-yourself.html
    """

    ROUTES_RE = re.compile(r'''
        \{              # The exact character "{"
        (\w+)           # The variable name (restricted to a-z, 0-9, _)
        (?::([^}]+))?   # The optional :regex part
        \}              # The exact character "}"
        ''', re.VERBOSE)


    @classmethod
    def parse_route(cls, template):
        regex = ''
        last_pos = 0

        for match in cls.ROUTES_RE.finditer(template):
            regex += re.escape(template[last_pos:match.start()])
            var_name = match.group(1)
            expr = match.group(2) or '[^/]+'
            expr = '(?P<%s>%s)' % (var_name, expr)
            regex += expr
            last_pos = match.end()

        regex += re.escape(template[last_pos:])
        regex = '^%s$' % regex

        return re.compile(regex)


    def __init__(self):
        self.LOG = pymagic.get_class_logger(self)
        self.routes = []

 
    def add_route(self, template, controller, **kwargs):
        if isinstance(controller, basestring):
            controller = pymagic.import_name(controller)

        self.routes.append((self.parse_route(template), controller, kwargs))

        return self


    def __call__(self, environ, start_response):
        req = Request(environ)
        self.LOG.debug("Incoming request at %r" % (req.path_info,))

        for regex, controller, kwargs in self.routes:
            match = regex.match(req.path_info)
            if match:
                req.urlvars = Bunch(kwargs)
                req.urlvars.update(match.groupdict())
                self.LOG.debug("controller=%r; vars=%r; req=%r; env=%r" % (controller, req.urlvars, req, environ))
                return controller(environ, start_response)

        return exc.HTTPNotFound()(environ, start_response)


@wsgify
def redirect(req, _log=pymagic.get_lazy_logger("redirect")):
    log = req.environ.get("wsgilog.logger", _log)
    to = req.relative_url(req.urlvars.to)
    log.info("Redirecting '%s' to '%s'" % (req.url, to))
    return exc.HTTPMovedPermanently(location=to)


def make_app(httpd_config):
    """ Factory for the monitoring webapp.
    """
    #mimetypes.add_type('image/vnd.microsoft.icon', '.ico')

    # Default paths to serve static file from
    htdocs_paths = [
        os.path.realpath(os.path.join(config.config_dir, "htdocs")),
        os.path.join(os.path.dirname(config.__file__), "data", "htdocs"),
    ]
    
    return (Router()
        .add_route("/", controller=redirect, to="/static/index.html")
        .add_route("/favicon.ico", controller=redirect, to="/static/favicon.ico")
        .add_route("/static/{filepath:.+}", controller=StaticFolders(htdocs_paths))
        .add_route("/json/{action}", controller=JsonController(**httpd_config.json))
    )


if __name__ == "__main__":
    import pprint
    from pyrocore import connect

    try:
        engine = connect()
        print("%s - %s" % (engine.engine_id, engine.open()))
        pprint.pprint(engine_data(engine))
        print("%s - %s" % (engine.engine_id, engine.open()))
    except (error.LoggableError, xmlrpc.ERRORS), torrent_exc:
        print("ERROR: %s" % torrent_exc)

