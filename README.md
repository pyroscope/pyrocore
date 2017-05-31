# pyrocore

[![Travis CI](https://travis-ci.org/pyroscope/pyrocore.svg?branch=master)](https://travis-ci.org/pyroscope/pyrocore)
[![Issues](https://img.shields.io/github/issues/pyroscope/pyrocore.svg)](https://github.com/pyroscope/pyrocore/issues)
[![PyPI](https://img.shields.io/pypi/v/pyrocore.svg)](https://pypi.python.org/pypi/pyrocore/)

This project provides a collection of tools for the BitTorrent protocol and especially the
[rTorrent client](https://github.com/rakshasa/rtorrent).
They enable you to filter rTorrent's item list for displaying or changing selected items,
also creating, inspecting and changing ``.torrent`` files, and much more.

An optional daemon process (``pyrotorque``) can add flexible queue management for rTorrent,
starting items added in bulk slowly over time according to customizable rules.
The same daemon can also watch one or more directory trees recursively for new metafiles using inotify,
resulting in instantaneous loading without any polling and no extra configuration for nested directories.

![rtcontrol + curses demo](https://raw.githubusercontent.com/pyroscope/pyroscope/master/pyrocore/docs/videos/rtcontrol-curses.gif)

The `PyroScope` command line utilities are *not* the same as the sibling project
[rTorrent-PS](https://github.com/pyroscope/rtorrent-ps),
and they work perfectly fine without it;
the same is true the other way 'round.
It's just that both unsurprisingly have synergies if used together,
and some features *do* only work when both are present.


Further information can be found in the
[documentation](http://pyrocore.readthedocs.io/), specifically:

 * [A feature overview](http://pyrocore.readthedocs.io/en/latest/overview.html)
 * [Installation instructions](http://pyrocore.readthedocs.io/en/latest/installation.html)
 * [Full API documentation](http://pyrocore.readthedocs.io/en/latest/api.html)

You can also add your own content to the
[project's wiki](https://github.com/pyroscope/pyrocore/wiki#community-documentation),
to help out other users, and show to the world you're awesome.

To get in contact and share your experiences with other users of *PyroScope*, join the
[pyroscope-users](http://groups.google.com/group/pyroscope-users)
mailing list or the inofficial ``##rtorrent`` channel on ``irc.freenode.net``.


## News

``Date   ``| Description
:-------------------: | :----
``31–May–2017`` | [pyrocore 0.5.2](https://github.com/pyroscope/pyrocore/releases/tag/v0.5.2) released.
``27–May–2017`` | [pyrocore 0.5.1](https://github.com/pyroscope/pyrocore/releases/tag/v0.5.1) released.
``05–Mar–2017`` | Moving and over-hauling the docs finally done, including rTorrent-PS wiki pages and so on.
``02–May–2015`` | Started to move the documenation to [Read The Docs](http://pyrocore.readthedocs.io/).
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


## Performing a Release

1. Check for and fix ``pylint`` violations:

        paver lint -m | egrep -v 'TODO|Too.many'

1. Verify ``debian/changelog`` for completeness and the correct version, and bump the release date:

        dch -r

1. Remove ‘dev’ version tagging from ``setup.cfg``, and perform a release check:

        sed -i -re 's/^(tag_[a-z ]+=)/##\1/' setup.cfg
        paver release

1. Commit and tag the release:

        git status  # check all is committed
        tag="v$(dpkg-parsechangelog | grep '^Version:' | awk '{print $2}')"
        git tag -a "$tag" -m "Release $tag"

1. Build the final release and upload it to PyPI:

        paver dist_clean sdist bdist_wheel
        twine upload dist/*.{zip,whl}

1. Create the ZIP file with the API documentation:

        paver autodocs
        # Make sure docs are built OK
        paver dist_docs

1. Upload the docs from the ``dist`` directory to ``pythonhosted.org``:

        xdg-open "https://pypi.python.org/pypi?%3Aaction=pkg_edit&name=pyrocore" &
