Overview
========

Introduction
------------

*pyrocore* is part of the `PyroScope`_ family of projects, and offers a
collection of tools for the :ref:`bt-protocol` and especially the
*rTorrent* client. This includes:

  * :ref:`command-line-tools` for automation of common tasks, like :ref:`metafile creation <mktor>`, and
    :ref:`filtering and mass-changing your loaded torrents <rtcontrol>`.
  * rTorrent extensions like a :ref:`QueueManager` and statistics (*work in progress*).
  * All this is based on the ``pyrocore`` Python package, that you can
    use to :ref:`scripts` for any special needs that aren't covered by
    the standard tools.

See the
`ScreenShotGallery <https://github.com/pyroscope/rtorrent-ps/blob/master/docs/ScreenShotGallery.md>`_
if you want to get a first impression without installing the software.

.. include:: include-contacts.rst

.. _`PyroScope`: https://github.com/pyroscope


.. _glossary:

Glossary
--------

To help you better understand this manual,
here are the definitions of some key concepts used in it.

(download) item
    An item loaded into rTorrent.

field
    An attribute of a download item, e.g. ``name``, ``completed``, and ``directory``.
    Most of these you know from *rTorrent* or *ruTorrent*, but *PyroScope* adds some of its own.
    They are used in conditions to filter items using the ``rtcontrol`` tool,
    and also name the things you want to print to the console when listing items.
    To get a full list, use the ``rtcontrol --help-fields`` command.

metafile
    The term *metafile* means the ``.torrent`` file – using 'torrent' is avoided intentionally,
    because it's often used ambiguously to mean *either* the metafile or the *data* of a download item.

XMLRPC
    The protocol used to remotely control a running rTorrent process.
    Note that support for XMLRPC is an option that must be activated when compiling
    the rTorrent binary, so make sure it's active in your installation
    when 'nothing works' for you. A quick way to check is calling the following command:

    .. code-block:: bash

        $ ldd $(command which rtorrent) | grep libxmlrpc.so
                libxmlrpc.so.3 => /home/pyroscope/.local/rtorrent/0.9.6-PS-1.0/lib/libxmlrpc.so.3 …


Quick Start Guide
-----------------

Work through these chapters in order to get the software up and running,
and to learn basic concepts of using the command line tools.

  * :doc:`installation`
  * :doc:`setup`
  * :doc:`usage`

Consult the :doc:`troubleshooting` if anything goes wrong.
:ref:`issue-reporting` explains how to provide feedback in case
you encounter a serious problem, or are missing a feature.

.. warning::

    If you do a fresh installation of *pyrocore* in addition to an existing
    *rTorrent* one, you will need to follow the instructions
    to :ref:`backfill-data`, which fills in some data your already
    running rTorrent instance is missing otherwise! So do **not**
    skip that section.


Further Information & Customization
-----------------------------------

  * :doc:`howto` highlights some specific use-cases and might
    give you some inspiration when solving your own problems.
  * Using :doc:`advanced` requires some knowledge in the area Linux,
    Bash, and Python beyond a novice level, but they enable you to
    customize your setup even further and handle very specific use-cases.
  * :doc:`custom` tells you about :ref:`scripts` as an easy way to automate anything
    that the standard commands can't do.
    There are more ways for adding your own custom logic,
    amongst them :ref:`CustomFields` for adding user-defined fields,
    available in ``rtcontrol`` just like built-in ones.
  * :doc:`updating` explains how to get newer versions
    of this software after the initial installation.
  * :doc:`references` provides details on technical background topics
    like XMLRPC, and links into the web with related information.
