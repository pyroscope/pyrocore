.. included from usage.rst

Introduction
^^^^^^^^^^^^

This section provides details on the use of the features that
are added by the :ref:`standard rTorrent configuration include <rtorrent-pyro-rc>`.
Many of them work on a vanilla release of rTorrent – but see the note below.

See also the `full list of additional features`_ in the rTorrent-PS documentation.
There's also some features that are located in the `pimp-my-box configuration includes`_,
which means in order to get them you either need to use that way of setup,
or follow the `Manual Turn-Key System Setup`_ instructions in the rTorrent-PS manual
(specifically the `rTorrent Configuration`_ part).

If you think this is too complicated and scattered all over the place,
the `pimp-my-box project`_ packages all this into a nicely integrated experience.
Just sayin'. ☺

If you don't want to use `Ansible`, then the `make-rtorrent-config.sh`_ script
gives you the same setup with a bit more manual work involved.

.. important::

    Any feature that mentions some form of custom key binding **does**
    require that you run a build of `rTorrent-PS`_!

.. _`rTorrent-PS`: https://github.com/pyroscope/rtorrent-ps
.. _`full list of additional features`: https://rtorrent-ps.readthedocs.io/en/latest/manual.html#features-std-cfg
.. _`pimp-my-box project`: https://pimp-my-box.readthedocs.io/
.. _`pimp-my-box configuration includes`: https://github.com/pyroscope/pimp-my-box/tree/master/roles/rtorrent-ps/templates/rtorrent/rtorrent.d
.. _`Manual Turn-Key System Setup`: https://rtorrent-ps.readthedocs.io/en/latest/install.html#debianinstallfromsource
.. _`rTorrent Configuration`: https://rtorrent-ps.readthedocs.io/en/latest/install.html#rtorrent-configuration
.. _`make-rtorrent-config.sh`: https://rtorrent-ps.readthedocs.io/en/latest/install.html#make-rtorrent-config


.. _std-cfg-misc:

Miscellaneous Features
^^^^^^^^^^^^^^^^^^^^^^

In this section, some smaller added features are mentioned
– quite often, their effects are not directly visible in the user interface.
When filenames are mentioned, they can be found in ``~/.pyroscope/rtorrent.d``
(look at the ``*.default`` files, those are up-to-date).

``auto-scrape.rc`` regularly updates scrape information for all torrents, even stopped ones.
It makes the peer counter columns show actually useful and reasonably up-to-date information.

``commands.rc`` adds convenience commands for the ``Ctrl-X`` prompt, like ``s=`` and ``t=``.

``logging.rc`` enables feedback on a few major events like completion,
announces day changes, and warns when the ``~/NOCRON`` flag file exists.

``quick-help.rc`` contains the help information shown when you press ``F2`` in `rTorrent-PS`.

``timestamps.rc`` records the time at which various events happen into custom fields.
This is the basis for sorting views like ``indemand`` or ``last_xfer``.


.. _additional-views:

Additional Views
^^^^^^^^^^^^^^^^

Custom Views: Key Bindings
""""""""""""""""""""""""""

Here's an overview of additonal views and view customizations that are
part of the standard configuration.

#.  The ``:`` key shows the ``tagged`` view, more on that one below.
#.  The ``t`` key is bound to a ``trackers`` view that shows all items
    sorted by tracker and then by name.
#.  The ``!`` key is bound to a ``messages`` view, listing all items
    that currently have a non-empty message, sorted in order of the
    message text.
#.  The ``^`` key is bound to the ``rtcontrol`` search result view, so
    you can easily return to your last search.
#.  The ``?`` key is bound to the ``indemand`` view, which sorts all
    open items by their activity (last time a peer was connected),
    with the most recently active on top.
#.  The ``%`` key is bound to the ``ratio`` view, which sorts all
    open items by their ratio (descending) – equal ratios sort by uploaded data.
#.  The ``°`` key is bound to the ``uploaded`` view, which sorts all
    open items by their total upload amount (descending).
#.  The ``"`` key is bound to the ``datasize`` view, which sorts all
    open items by the size of their content data (descending).
#.  The ``¬`` key (``AltGr+^`` on some keyboards) is bound to the ``last_xfer`` view,
    which sorts all items by their *last_xfer* + *active* timestamps, or else event times.

For the ``uploaded`` and ``ratio`` view, there's a tail of items with zero values.
That is sorted by completed / loaded / downloaded event timestamps,
with the first non-zero time used.

If certain key bindings are not convenient or even accessible for you (say ``°`` and ``¬``),
define your own *in addition* in ``_rtlocal.rc`` or a similar customization file.

.. code-block:: ini

    # Bind last_xfer / uploaded views to F5 / F6
    pyro.bind_key = my_last_xfer_view, 0415, \
        "view.sort = last_xfer ; ui.current_view.set = last_xfer"
    pyro.bind_key = my_uploaded_view, 0416, \
        "view.sort = uploaded ; ui.current_view.set = uploaded"

The `Extended Canvas Explained`_ section in the `rTorrent-PS` manual has a list
of columns in those view, and what they mean.

.. _`Extended Canvas Explained`: https://rtorrent-ps.readthedocs.io/en/latest/manual.html#extended-canvas


.. _view-tagged:

The `tagged` View
"""""""""""""""""

The ``.`` key toggles the membership in the ``tagged`` view for the
item in focus, ``:`` shows the ``tagged`` view, and ``T`` clears
that view (i.e. removes the tagged state on all items). This can be
very useful to manually select a few items and then run
``rtcontrol`` on them, or alternatively use ``--to-view tagged`` to
populate the ``tagged`` view, then deselect some items interactively
with the ``.`` key, and finally mass-control the rest.

**TODO** More detail


.. _view-active:

Modified `active` View
""""""""""""""""""""""

The ``active`` view is changed to include all incomplete items
regardless of whether they have any traffic, and then groups the
list into complete, incomplete, and queued items, in that order.
Within each group, they're sorted by download and then upload speed.

.. hint::

    This feature is added by ``views.rc`` in the `pimp-my-box configuration includes`_.


.. _color-themes:

.. _category-views:

Category Views
""""""""""""""

The ``<`` and ``>`` keys rotate through all added category views
(``pyro.category.add=‹name›``), with filtering based on the
ruTorrent label (``custom_1=‹name›``).

``|`` re-applies the category filter and thus updates the current
category view.

See :ref:`howto-categories` for more details.


Color Themes
^^^^^^^^^^^^

The ``~`` key rotates through all available color themes,
or a user-selected subset of them.

Here are screen shots of some of the default schemes
– from left to right: Default (256 xterm colors), Happy Pastel, Solarized Blue, and Solarized Yellow.

|color-scheme-default|   |color-scheme-happy-pastel|

|color-scheme-solarized-blue|   |color-scheme-solarized-yellow|

What they actually look like depends on the color palette of your terminal,
so adapt the examples to your liking and terminal setup.

Read more on the configuration of color schemes
and the necessary setup of `rTorrent-PS` in its
`Color Scheme Configuration`_ section of the manual.

**TODO** More details (theme directory, theme selection, …)

.. _`Color Scheme Configuration`: https://rtorrent-ps.readthedocs.io/en/latest/setup.html#color-schemes

.. |color-scheme-default| image:: https://rtorrent-ps.readthedocs.io/en/latest/_images/color-scheme-default.png
    :width: 320px
.. |color-scheme-happy-pastel| image:: https://rtorrent-ps.readthedocs.io/en/latest/_images//color-scheme-happy-pastel.png
    :width: 320px
.. |color-scheme-solarized-blue| image:: https://rtorrent-ps.readthedocs.io/en/latest/_images//color-scheme-solarized-blue.png
    :width: 320px
.. |color-scheme-solarized-yellow| image:: https://rtorrent-ps.readthedocs.io/en/latest/_images//color-scheme-solarized-yellow.png
    :width: 320px


.. _watch-start:

Watches With Dynamic Start
^^^^^^^^^^^^^^^^^^^^^^^^^^

The new ``d.watch.startable`` and ``load.category`` commands allow you to easily change
whether an item loaded by a watch is started immediately (the default), or not.

This is especially useful when combined with automatic downloaders like `FlexGet`_ or `autodl-irssi`_.
Usually, newly added items are started immediately – that is the whole point of automation.

In some cases though, you might want to disable that and delay downloading until later.
Testing configuration changes is a typical reason, because an innocent mistake could
swamp you with lots of downloads. If they stay dormant at first, that is easily fixed.

Just call ``rtxmlrpc -i cfg.watch.start.set=0`` and you get exactly that, *without* a rTorrent restart.
If everything looks OK, re-enable instant downloading by changing the ``0`` to ``1`` again.
Calling ``rtcontrol --from stopped done=0 custom_watch_start=1 --start`` will start anything added in the meantime.

To get such a watch directory, add a schedule like this to your configuration:

.. code-block:: ini

    schedule2 = watch_dynamic, 10, 10, \
        ((load.verbose, (cat, (cfg.watch), "dynamic/*.torrent"), "d.watch.startable="))

It is important to either use ``load.verbose`` or ``load.normal`` so the item stays idle,
and then add the post-load ``d.watch.startable`` command to mark this item as eligible to be started.

The ``load.category`` command (added by `rtorrent.d/categories.rc`_) already integrates
this behaviour. It can be used like shown in this example:

.. code-block:: ini

    schedule2 = watch_hdtv, 10, 10, ((load.category, hdtv))

See :ref:`category-views` for more on categories.


.. topic:: Technical Details

    Since you cannot call ``d.start`` as a post-load command (the item is not fully initialized yet),
    the conditional start has to happen *after* the load is finished.

    Therefor, a ``event.download.inserted_new`` handler checks for the custom attribute ``watch_start``
    set by ``d.watch.startable`` (thus only acting on items loaded by specifically marked watch schedules),
    and then continues to call ``d.start`` *only if* the ``cfg.watch.start`` value is currently set to ``1``.

    See the `rtorrent.d/00-default.rc`_ file for the full command definitions.


.. _`FlexGet`: https://flexget.com/
.. _`autodl-irssi`: https://github.com/autodl-community/autodl-irssi
.. _`rtorrent.d/categories.rc`: https://github.com/pyroscope/pyrocore/blob/master/src/pyrocore/data/config/rtorrent.d/categories.rc
.. _`rtorrent.d/00-default.rc`: https://github.com/pyroscope/pyrocore/blob/master/src/pyrocore/data/config/rtorrent.d/00-default.rc
