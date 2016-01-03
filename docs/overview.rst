Overview
========

Introduction
------------

*pyrocore* is part of the `PyroScope`_ family of projects, and offers a
collection of tools for the :ref:`bt-protocol` and especially the
*rTorrent* client. This includes:

  * `CommandLineTools <https://github.com/pyroscope/pyroscope/blob/wiki/CommandLineTools.md>`_
    for automation of common tasks, like metafile creation, and
    `filtering and mass-changing your loaded
    torrents <https://github.com/pyroscope/pyroscope/blob/wiki/RtControlExamples.md>`_.
  * rTorrent extensions like a
    `QueueManager <https://github.com/pyroscope/pyroscope/blob/wiki/QueueManager.md>`_
    and statistics (*work in progress*).
  * All this is based on the ``pyrocore`` Python package, that you can
    use to :doc:`scripts` for any special needs that aren't covered by
    the standard tools.

See the
`ScreenShotGallery <https://github.com/pyroscope/pyroscope/blob/wiki/ScreenShotGallery.md>`_
if you want to get a first impression without installing the software.

To get in contact and share your experiences with other users of
*PyroScope*, join the `pyroscope-users`_ mailing list or the inofficial
``##rtorrent`` channel on ``irc.freenode.net``.

.. _`PyroScope`: https://github.com/pyroscope
.. _`pyroscope-users`: http://groups.google.com/group/pyroscope-users


Quick Start Guide
-----------------

Work through these chapters in order to get the software up and running,
and to learn basic concepts of using the command line tools.

  * :doc:`installation`
  * :doc:`setup`
  * :doc:`usage`

Consult the :doc:`troubleshooting` if anything goes wrong.


Customization
-------------

  * :ref:`CustomFields` allows you to add user-defined fields,
    available in ``rtcontrol`` just like built-in ones.
  * :doc:`scripts` is an easy way to automate anything that the standard commands can't do.
