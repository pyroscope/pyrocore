#! /usr/bin/env python-pyrocore
# -*- coding: utf-8 -*-
import sys
import subprocess

import pandas as pd

from pyrobase.osutil import shell_escape as quoted

from pyrocore import config
from pyrocore.scripts import base


class HeatMap(base.ScriptBase):
    """
        Create a heatmap based on JSON data generated via `rtcontrol`.

        THIS IS EXPERIMENTAL, THERE'S NO SUPPORT WHATSOEVER!

        To run this script, you need to first install `seaborn`:

            ~/.local/pyroscope/bin/pip install seaborn

        Then, try this:

            rtcontrol --json -qo name,alias,ratio -A dupes= loaded=-1w \
                | docs/examples/rt-heapmap.py -o name alias ratio

            rtcontrol --json -qo tv_series,alias,ratio -A dupes= ratio=+4 loaded=-6m tv_series=\! \
                | docs/examples/rt-heapmap.py -o tv_series alias ratio
    """

    # argument description for the usage information
    ARGS_HELP = "<index> <column> <value>"

    # set your own version
    VERSION = '1.0'

    # (optionally) define your licensing
    COPYRIGHT = u'Copyright (c) 2018 PyroScope Project'

    # Minimum upper range for color map
    CMAP_MIN_MAX = 4.0


    def add_options(self):
        """ Add program options.
        """
        super(HeatMap, self).add_options()

        # basic options
        self.add_bool_option('-o', '--open',
            help="open the resulting image file in your viewer")

    def heatmap(self, df, imagefile):
        """ Create the heat map.
        """
        import seaborn as sns
        import matplotlib.ticker as tkr
        import matplotlib.pyplot as plt
        from  matplotlib.colors import LinearSegmentedColormap

        sns.set()
        with sns.axes_style('whitegrid'):
            fig, ax = plt.subplots(figsize=(5, 11))  # inches

            cmax = max(df[self.args[2]].max(), self.CMAP_MIN_MAX)
            csteps = {
                0.0: 'darkred', 0.3/cmax: 'red', 0.6/cmax: 'orangered', 0.9/cmax: 'coral',
                1.0/cmax: 'skyblue', 1.5/cmax: 'blue', 1.9/cmax: 'darkblue',
                2.0/cmax: 'darkgreen', 3.0/cmax: 'green',
                (self.CMAP_MIN_MAX - .1)/cmax: 'palegreen', 1.0: 'yellow'}
            cmap = LinearSegmentedColormap.from_list('RdGrYl', sorted(csteps.items()), N=256)

            dataset = df.pivot(*self.args)

            sns.heatmap(dataset, mask=dataset.isnull(), annot=False, linewidths=.5, square=True, ax=ax, cmap=cmap,
                        annot_kws=dict(stretch='condensed'))
            ax.tick_params(axis='y', labelrotation=30, labelsize=8)
            # ax.get_yaxis().set_major_formatter(tkr.FuncFormatter(lambda x, p: x))
            plt.savefig(imagefile)

    def mainloop(self):
        """ The main loop.
        """
        #proxy = config.engine.open()

        if len(self.args) != 3:
            self.fatal("You MUST provide names for index (row), column, and value!")

        # Load data
        df = pd.read_json(sys.stdin, orient='records')
        df[self.args[0]] = df[self.args[0]].str.slice(0, 42)
        #print(df[self.args[0]])
        #print(df.head(5))
        df = df.groupby(self.args[:2], as_index=False).mean()

        # Create image
        imagefile = 'heatmap.png'
        self.heatmap(df, imagefile)

        # Optionally show created image
        if self.options.open:
            subprocess.call("xdg-open {} &".format(quoted(imagefile)), shell=True)

        #self.LOG.info("XMLRPC stats: %s" % proxy)


if __name__ == "__main__":
    base.ScriptBase.setup()
    HeatMap().run()
