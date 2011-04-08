import time
import datetime

#import gtk
#import cairo
import pango
import gobject

import screenlets
from screenlets import options as opt


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
        self._content = datetime.datetime.fromtimestamp(time.time()).isoformat(' ')[:19]
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

        # compute space between fields
        ctx.set_source_rgba(*self.text_color)
        self.draw_text(ctx, self._content, 10,10,  "FreeSans",10, self.width-20,
            allignment=pango.ALIGN_LEFT,justify = True, weight=0)

    
    def on_draw_shape(self, ctx):
        self.on_draw(ctx)


def run():
    """ If the program is run directly or passed as an argument to the python
        interpreter then create a Screenlet instance and show it.
    """
    from screenlets import session
    session.create_session(PyroScopeScreenlet)
