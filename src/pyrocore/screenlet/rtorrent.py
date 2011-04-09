# -*- coding: utf-8 -*-
""" PyroCore - RTorrent Screenlet.

    Copyright (c) 2011 The PyroScope Project <pyroscope.project@gmail.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
from __future__ import with_statement

import os
import socket
from contextlib import contextmanager

#import gtk
#import cairo
import pango
import gobject

import screenlets
from screenlets import options as opt

from pyrocore.util import xmlrpc
from pyrocore.torrent import formatting


# TODO: Add up/down meter (graphed)
# TODO: Number of items in views (incomplete / stopped / etc)
# TODO: (Number of) Tracker messages
# TODO: Events (completed, loaded, etc), possibly using libnotify / growl
# TODO: Log displays (expandable, show last line or last update time only, by default)

class RtorrentState(object):
    """ Representation of current RTorrent state.
    """

    TEMPL = '\n'.join(["{{#}}"
        "rT {{d.version}} - {{d.engine_id}} - up {{d.uptime | duration | strip}}",
        "",
        u"U: {{d.up_rate | sz}} / {{d.up_throttle | sz}} \u03a3{{d.up_size | sz}}",
        u"D: {{d.down_rate | sz}} / {{d.down_throttle | sz}} \u03a3{{d.down_size | sz}}",
        "",
        "E: {{d.error}}",
    ])


    def __init__(self, scgi_url):
        self.scgi_url = scgi_url
        self._proxy = xmlrpc.RTorrentProxy(self.scgi_url)
        self.error = ""

        self.time           = 0
        self.uptime         = 0
        self.startup        = 0
        self.down_size      = 0
        self.down_rate      = 0
        self.down_throttle  = 0
        self.up_size        = 0
        self.up_rate        = 0
        self.up_throttle    = 0
        
        with self.transaction() as proxy:
            self.engine_id = proxy.get_name()
            self.version = "%s/%s" % (
                proxy.system.client_version(), 
                proxy.system.library_version(),
            )
            self.time = proxy.system.time_seconds()

            try:
                self.startup = os.path.getmtime(os.path.join(proxy.get_session().rstrip(os.sep), "rtorrent.lock"))
            except EnvironmentError, exc:
                print "Can't get start time: %s" % exc


    @contextmanager
    def transaction(self):
        """ Do a safe transaction with the client.
        """
        try:
            yield self._proxy
        except socket.error, exc:
            self.error = "Transaction error with %s: %s" % (self.scgi_url, exc)
        except Exception, exc:
            self.error = "Transaction error with %s: %s" % (self.scgi_url, exc)


    def update(self):
        """ Do a minor update on values that are cheap to get.
        """
        with self.transaction() as proxy:
            self.time           = proxy.system.time_seconds()
            self.down_size      = proxy.get_down_total()
            self.down_rate      = proxy.get_down_rate()
            self.down_throttle  = proxy.get_download_rate()
            self.up_size        = proxy.get_up_total()
            self.up_rate        = proxy.get_up_rate()
            self.up_throttle    = proxy.get_upload_rate()
            
            self.error = ""

        if self.startup:
            self.uptime = self.time - self.startup


    def poll(self):
        """ Do a full poll of all download items and their state.
        """
        self.update()
        # TODO: implement!


class PyroScopeScreenlet(screenlets.Screenlet):
    """PyroScope Status Display"""
    
    # default meta-info for Screenlets
    __name__    = "PyroScopeScreenlet"
    __version__ = "0.1"
    __author__  = "2011 by pyroscope"
    __desc__    = __doc__

    # class objects
    __timeout = None
    _content = ""

    # Options
    update_interval     = 10
    poll_interval       = 60
    show_net_graphs     = True

    # Appearance
    w                   = 350
    h                   = 100
    frame_color         = (0, 0, 0, 0.7)
    inner_frame_color   = (0, 0, 0, 0.3)
    shadow_color        = (0, 0, 0, 0.5)
    text_color          = (1, 1, 1, 0.9)

    OPTIONS = [
        ("Appearance", "Settings changing the visualization on screen.", [
            (opt.IntOption, "w", "Width", "Width of canvas", dict(min=10, max=10000)),
            (opt.IntOption, "h", "Height", "Height of canvas", dict(min=10, max=10000)),
            (opt.ColorOption, "frame_color", "Background frame color", "Background frame color"),
            (opt.ColorOption, "inner_frame_color", "Inner frame color", "Inner frame color"),
            (opt.ColorOption, "shadow_color", "Shadow color", "Shadow color"),
            (opt.ColorOption, "text_color", "Text color", "Text color"),
        ]),
        ("Content", "Settings regarding the Screenlet content.", [
            (opt.IntOption, "update_interval", "Update interval [seconds]", 
             "The interval for global status refreshing (in seconds)", dict(min=2, max=3600)),
            (opt.IntOption, "poll_interval", "Poll interval [seconds]", 
             "The interval for polling download items information (in seconds)", dict(min=30, max=3600)),
            (opt.BoolOption, "show_net_graphs", "Show network I/O graphs", 
             "Show bandwidth graphs in addition to the current numbers"),
        ]),
    ]


    def __init__(self, **kw):
        screenlets.Screenlet.__init__(self, width=PyroScopeScreenlet.w, height=PyroScopeScreenlet.h,
            ask_on_option_override=False, **kw)

        # Set theme
        self.theme_name = "default"

        # Add options
        for group, help, options in self.OPTIONS:
            self.add_options_group(group, help)

            for option in options:
                opt_type, attr, label, tooltip = option[:4]
                opt_kw = {} if len(option) < 5 else option[4]
                self.add_option(opt_type(group, attr, getattr(self, attr), label, tooltip, **opt_kw)) 

        # Initial update
        # TODO: connection URL must be an option
        self.state = RtorrentState("scgi:///var/torrent/.scgi_local")
        self.set_update_interval()
        self.update()


    def __setattr__(self, name, value):
        screenlets.Screenlet.__setattr__(self, name, value)

        if name == "update_interval":
            self.set_update_interval(value)
        elif name == "w":
            self.width = value
        elif name == "h":
            self.height = value


    def set_update_interval(self, seconds=None):
        if seconds:
            seconds = max(2, seconds)
            self.__dict__["update_interval"] = seconds
        if self.__timeout:
            gobject.source_remove(self.__timeout) #@UndefinedVariable
        self.__timeout = gobject.timeout_add(int(self.update_interval * 1000), self.update) #@UndefinedVariable


    def update(self):
        self.state.update()
        self._content = formatting.format_item(self.state.TEMPL, self.state)
        self.redraw_canvas()
        return True

            
    def on_init(self):
        self.add_default_menuitems()


    def on_draw(self, ctx):
        # if a converter or theme is not yet loaded, there"s no way to continue
        # set scale relative to scale-attribute
        ctx.scale(self.scale, self.scale)

        # render background
        ctx.set_source_rgba(*self.frame_color)
        self.draw_rectangle_advanced (ctx, 0, 0, self.width-12, self.height-12, 
            rounded_angles=(5,)*4, fill=True, 
            border_size=2, border_color=self.inner_frame_color, 
            shadow_size=6, shadow_color=self.shadow_color)
        #self.theme["background.svg"].render_cairo(ctx)

        # render text
        ctx.set_source_rgba(*self.text_color)
        # TODO: make font an option
        self.draw_text(ctx, self._content, 10,10,  "DejaVu Sans Mono",9, self.width-20,
            allignment=pango.ALIGN_LEFT, justify=True, weight=0)

    
    def on_draw_shape(self, ctx):
        self.on_draw(ctx)


def run():
    """ If the program is run directly or passed as an argument to the python
        interpreter, then create a Screenlet instance and show it.
    """
    from screenlets import session
    session.create_session(PyroScopeScreenlet)
