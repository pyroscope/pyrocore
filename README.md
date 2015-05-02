# pyrocore

A collection of tools for the BitTorrent protocol and especially the rTorrent client.

![rtcontrol + curses demo](https://raw.githubusercontent.com/pyroscope/pyroscope/master/pyrocore/docs/videos/rtcontrol-curses.gif)

The `PyroScope` command line utilities are *not* the same as
[rTorrent-PS](https://github.com/pyroscope/rtorrent-ps),
and they work perfectly fine without it;
the same is true the other way 'round.
It's just that both unsurprisingly have synergies if used together,
and some features *do* only work when both are present.


Further information can be found in the
[documentation](http://pyrocore.readthedocs.org/), specifically:

 * [A feature overview](http://pyrocore.readthedocs.org/en/latest/overview.html)
 * [Installation instructions](http://pyrocore.readthedocs.org/en/latest/installation.html)
 * [Full API documentation](http://pyrocore.readthedocs.org/en/latest/api.html)


## News

Date     | Description
:-------------------: | :----
``02–May–2015`` | Started to move the documenation to [Read The Docs](http://pyrocore.readthedocs.org/).
``14–Mar–2015`` | Moved from [Google Code](https://code.google.com/p/pyroscope/ ) to [GitHub](https://github.com/pyroscope/pyroscope). Documentation will be in a limbo state and spread over both sites for some time, I'll try to reasonably cross-link.
``05–Jun–2011`` | [pyrocore 0.4.2](http://freshmeat.net/projects/pyrocore/releases/332769) released.
``17–Apr–2011`` | [pyrocore 0.4.1](http://freshmeat.net/projects/pyrocore/releases/331021) released.
``05–Mar–2011`` | [pyrocore 0.3.10](http://freshmeat.net/projects/pyrocore/releases/329060) released.
``05–Sep–2010`` | [pyrocore 0.3.7](http://pypi.python.org/pypi?:action=display&name=pyrocore&version=0.3.7) released, offering automatic classification for completion paths, a working `rtmv` in symlinked mode, grouping of filter conditions, rTorrent fast-resume support, and better cron logging.
``29–Aug–2010`` | [pyrocore 0.3.6](http://pypi.python.org/pypi?:action=display&name=pyrocore&version=0.3.6) released, featuring more torrent life-cycle fields, selecting into rTorrent views, file listings and filtering based on file type, and finer control over formatting pathname fields.
``28–Aug–2010`` | Published the [API documentation](http://packages.python.org/pyrocore/apidocs/index.html) in Javadoc style including class diagrams and cross-referenced source code.
``20–Aug–2010`` | [pyrocore 0.3.5](http://pypi.python.org/pypi?:action=display&name=pyrocore&version=0.3.5) released, adding custom attributes and item tagging, and column headers to result listings.
``16–Aug–2010`` | [pyrocore 0.3.4](http://pypi.python.org/pypi?:action=display&name=pyrocore&version=0.3.4) released, with a finished `chtor` and new `rtxmlrpc` tool, additional fields containing load and completion time, and action options to delete or throttle items, or put them under manual control.
``20–Mar–2010`` | [pyrocore 0.3.3](http://pypi.python.org/pypi?:action=display&name=pyrocore&version=0.3.3) released, including many new `chtor` options, and some `rtcontrol` improvements.
``14–Mar–2010`` | [pyrocore 0.3.2](http://pypi.python.org/pypi?:action=display&name=pyrocore&version=0.3.2) released, allowing you to mass-start/stop items in a selection result.
``13–Mar–2010`` | [pyrocore 0.3.1](http://pypi.python.org/pypi?:action=display&name=pyrocore&version=0.3.1) released, adding filtering, sorting and output formatting to `rtcontrol`.
``08–Mar–2010`` | [pyrocore 0.2.1](http://pypi.python.org/pypi?:action=display&name=pyrocore&version=0.2.1) released, with new tools `chtor` and `pyroadmin`, and a finished configuration system.
``19–Feb–2010`` | First release of `pyrocore` ([v0.1.1](http://pypi.python.org/pypi?:action=display&name=pyrocore&version=0.1.1)), containing the `lstor` and `mktor` utilities.
