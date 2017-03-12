.. pyrocore documentation master file, created by
   sphinx-quickstart on Sat May  2 16:17:52 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: _static/img/logo.png

Welcome to pyrocore's documentation!
====================================

*pyrocore* is a collection of tools for the BitTorrent protocol
and especially the rTorrent client.
They enable you to filter rTorrent's item list for displaying or changing selected items,
also creating, inspecting and changing ``.torrent`` files, and much more.

An optional daemon process named ``pyrotorque`` can add flexible queue management for rTorrent,
starting items added in bulk slowly over time according to customizable rules.

It can also watch a directory tree recursively for new metafiles using *inotify*.
That means ``.torrent`` files you drop anywhere into that watched tree are loaded instantaneously,
without any polling and no extra configuration for nested directories.

.. note::

    The *PyroScope* command line utilities (i.e. *pyrocore*) are *not* the same as `rTorrent-PS`_,
    and they work perfectly fine without it; the same is true the other
    way 'round.
    It's just that both projects unsurprisingly have synergies if used together,
    and some features *do* only work when both are present.

You absolutely **must** read the first three chapters
:doc:`overview`, :doc:`installation`, and :doc:`setup`
̣— *pyrocore* utilities won't work at all or not properly if
you do not provide an adequate configuration, and also modify
the *rTorrent* one to provide some essential data and commands.
Once you got everything basically working, :doc:`usage`
will show you all the common commands and use-cases. Further chapters then explain
more complex use-cases and features that might not appeal or apply to you.

.. include:: include-contacts.rst


Contents of This Manual
-----------------------

..    :caption: First Steps
..  toctree::
    :maxdepth: 4

    overview
    installation
    setup
    usage

..    :caption: Advanced Usage
..  toctree::
    :maxdepth: 4

    howto
    advanced
    experimental
    custom
    troubleshooting
    updating

..    :caption: References
..  toctree::
    :maxdepth: 4

    references
    api
    contributing
    license


Indices & Tables
----------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
