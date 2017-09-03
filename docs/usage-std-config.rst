.. included from usage.rst

This section provides details on the use of the features that
are added by the :ref:`standard configuraiton include <rtorrent-pyro-rc>`.
Many of them work on a vanilla release of rTorrent – but see the note below.

See also the `full list of additional features`_ in the rTorrent-PS documentation.
There's also some features that are located in the `pimp-my-box configuration includes`_,
which means in order to get them you either need to use that way of setup,
or follow the `Manual Turn-Key System Setup`_ instructions in the rTorrent-PS manual
(specifically the `rTorrent Configuration`_ part).

If you think this is too complicated and scattered all over the place,
the `pimp-my-box project`_ packages all this into a nicely integrated experience.
Just sayin'. ☺


.. important::

    Any feature that mentions some form of custom key binding **does**
    require that you run a build of `rTorrent-PS`_!

.. _`rTorrent-PS`: https://github.com/pyroscope/rtorrent-ps
.. _`full list of additional features`: https://rtorrent-ps.readthedocs.io/en/latest/manual.html#features-std-cfg
.. _`pimp-my-box project`: https://pimp-my-box.readthedocs.io/
.. _`pimp-my-box configuration includes`: https://github.com/pyroscope/pimp-my-box/tree/master/roles/rtorrent-ps/templates/rtorrent/rtorrent.d
.. _`Manual Turn-Key System Setup`: https://rtorrent-ps.readthedocs.io/en/latest/install.html#debianinstallfromsource
.. _`rTorrent Configuration`: https://rtorrent-ps.readthedocs.io/en/latest/install.html#rtorrent-configuration


.. _std-cfg-misc:

Miscellaneous Features
^^^^^^^^^^^^^^^^^^^^^^

In this section, some smaller added features are mentioned
– quite often, their effects are not directly visible in the user interface.

**TODO** Details


.. _additional-views:

Additional Views
^^^^^^^^^^^^^^^^

Here's an overview of additonal views and view customizations that are
part of the standard configuration.

#.  the ``t`` key is bound to a ``trackers`` view that shows all items
    sorted by tracker and then by name.
#.  the ``!`` key is bound to a ``messages`` view, listing all items
    that currently have a non-empty message, sorted in order of the
    message text.
#.  the ``^`` key is bound to the ``rtcontrol`` search result view, so
    you can easily return to your last search.
#.  the ``?`` key is bound to the ``indemand`` view, which sorts all
    open items by their activity, with the most recently active on top.

**TODO** Missing details?!


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

Color Themes
^^^^^^^^^^^^

The ``~`` key rotates through all available color themes,
or a user-selected subset of them.

**TODO** Details (theme directory, theme selection, screen thumbs, …)


.. _category-views:

Category Views
^^^^^^^^^^^^^^

The ``<`` and ``>`` keys rotate through all added category views
(``pyro.category.add=‹name›``), with filtering based on the
ruTorrent label (``custom_1=‹name›``).

``|`` re-applies the category filter and thus updates the current
category view.

**TODO** Details (``load.category`` commands, …)


.. _watch-start:

Watches With Dynamic Start Behaviour
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

The ``load.category`` command (added by ``rtorrent.d/categories.rc``) already integrates
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

    See the ``rtorrent.d/00-default.rc`` file for the full command definitions.


.. _`FlexGet`: https://flexget.com/
.. _`autodl-irssi`: https://github.com/autodl-community/autodl-irssi
