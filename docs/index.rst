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

An optional daemon process named :command:`pyrotorque` can add flexible queue management for rTorrent,
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
:doc:`overview`, :doc:`installation`, and :doc:`setup`,
and follow their instructions.
Otherwise *pyrocore* utilities won't work at all or not properly,
if you do not provide an adequate :file:`config.ini` file, and also modify
the *rTorrent* one to provide some essential data and commands.

Once you got everything basically working, :doc:`usage`
will show you all the common commands and use-cases. Further chapters then explain
more complex use-cases and features that might not appeal or apply to you.

.. include:: include-contacts.rst


Contents of This Manual
=======================

..  toctree::
    :maxdepth: 2
    :caption: Getting Started

    overview
    installation
    setup
    usage

..  toctree::
    :maxdepth: 2
    :caption: Advanced Usage

    howto
    advanced
    custom

..  toctree::
    :maxdepth: 2
    :caption: Other Topics

    troubleshooting
    updating
    tempita
    references
    license

..  toctree::
    :maxdepth: 2
    :caption: Development

    experimental
    api
    contributing


Indices & Tables
----------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
