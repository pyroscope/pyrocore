Tips & How-Tos
==============

Adding Category Views to the rTorrent UI
----------------------------------------

Version ``0.5.1`` enables you to easily add category views,
that also play nice with *ruTorrent* labels in ``custom_1``.
Since this relies on key bindings, it only works using *rTorrent-PS*.

First, you need to define your category names and watches,
like in this example:

.. code-block:: shell

    cd ~/rtorrent
    ~/.local/pyroscope/src/scripts/add-categories.sh books hdtv movies

It is recommended to stick to alphanumeric category names,
and use ``_`` for word separation.

The watches put loaded items into the given category,
and they expect metafiles in ``~/rtorrent/watch/‹category-name›``.

To remove a category, just edit it out of the ``rtorrent.d/categories.rc`` file,
and then call the ``add-categories.sh`` script without any arguments to clean things up.

On an existing installation, to auto-create categories for all the *ruTorrent* labels
you already have (and that also fit the *alphanumeric* constraint), call this:

.. code-block:: shell

    cd ~/rtorrent
    ~/.local/pyroscope/src/scripts/add-categories.sh \
        $(rtcontrol custom_1=\! -qo custom_1 | egrep '^[_a-zA-Z0-9]+$' | sort -u)


.. note::

    After these configuration changes, don't forget to restart *rTorrent*.


In the *rTorrent-PS* user interface, you can now work with the following keys:

 * Rotate through category views using ``<`` and ``>``.
 * The ``|`` key updates the current category view, i.e. filters for new or removed items.

The sort order of these views is the same as ``main``,
and if you switch to any other view and back to categories,
you always start at the first category view
(from the sorted list of category names).


Dumping Items as a JSON Array
-----------------------------

If you want to access rTorrent item data in machine readable form via ``rtcontrol``,
you can use its ``--json`` option and feed the output into another script parsing
the JSON data for further processing.

Here's an example:

.. code-block:: shell

    $ rtcontrol --json -qo name,is_ghost,directory,fno foo
    [
      {
        "directory": "/var/torrent/load/foo",
        "fno": 1,
        "is_ghost": false,
        "name": "foo"
      }
    ]

.. note::

    When using ``--json``, the list of fields given with ``-o`` must
    consist only of plain field names, i.e. format specifiers aren't supported.
    If you need derived values, the process parsing the output needs to calculate them.


Working With Several rTorrent Instances
---------------------------------------

Switching to the 'rtorrent.rc' of an Instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Both ``rtcontrol`` and ``rtxmlrpc`` read the existing rTorrent configuration
to extract some settings, so that you don't need to maintain them twice – most
importantly the details of the XMLRPC connection. That is why ``config.ini``
has the ``rtorrent_rc`` setting, and changing that is the key to select
a different instance you have running.

Just pass the option ``-D rtorrent_rc=PATH_TO/rtorrent.rc`` to either
``rtcontrol`` or ``rtxmlrpc``, to read the configuration of another instance
than the default one. For convenient use on the command line, you can add
shell aliases to you profile.

Customizing the Default Configuration per Instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since version ``0.5.1``, the extensions to the rTorrent configuration are
loaded via the commands in ``~/.pyroscope/rtorrent-pyro.rc.default``,
importing snippets found in the ``~/.pyroscope/rtorrent.d/`` directory.
The ``commands.rc.default`` file located there contains commands that use
``rtcontrol`` behind the scenes.

As shown in the previous section, these commands must use ``-D`` to load the
right configuration. Instead of switching to importing the ``*.rc`` variants
wholesale, with all the work that comes with that after updates,
you can simply ignore just the ``commands.rc.default`` file,
and replace it with an adapted copy in your *main* configuration file.

So, in summary, to customize a ``~/rtorrent1`` instance:

.. code-block:: shell

    echo >>~/.pyroscope/rtorrent.d/.rcignore "commands.rc.default"
    sed -r -e 's:--detach:--detach,-D,"rtorrent_rc=~/rtorrent1/rtorrent.rc":' \
        ~/.pyroscope/rtorrent.d/commands.rc.default \
        >>~/rtorrent1/rtorrent.rc

Now commands like ``s=`` are defined in ``~/rtorrent1/rtorrent.rc``, and
``commands.rc.default`` is not imported, so no duplicate definition errors occur.


Moving All Data for Selected Items to a New Location
----------------------------------------------------

This shows how to move the *data* of all items for a specific tracker
(identified by the alias ``TRK``) from ``~/rtorrent/data/`` to ``~/rtorrent/data/tracker/``.
Note that you can do that in *ruTorrent* too, but with too many items, or items too big,
the results vary (data is not or only partially moved).

This sequence of commands will stop and relocate the loaded items, move their data,
and finally start everything again.

.. code-block:: shell

    mkdir -p ~/rtorrent/data/tracker
    rtcontrol --to-view tagged alias=TRK realpath=$HOME/rtorrent/data
    rtcontrol --from-view tagged // --stop
    rtcontrol --from-view tagged // --exec "directory.set=$HOME/rtorrent/data/tracker" --yes
    rtcontrol --from-view tagged // --spawn "mv {{item.path}} $HOME/rtorrent/data/tracker"
    rtcontrol --from-view tagged // --start

By changing the first ``rtcontrol`` command that populates the ``tagged`` view,
you can change this to move data for any criteria you can think of — within the
limits of ``rtcontrol`` :ref:`filter-conditions`. Also, if you run *rTorrent-PS*, you can manually
remove items from the ``tagged`` view by using the ``.`` key, before applying the
rest of the commands.

Also see the :ref:`advanced-rtcontrol` section that explains
the ``--spawn`` and ``--exec`` options in more depth.

.. note::

    The ``tagged`` view is used here solely for the purpose of allowing
    manual manipulation of the search result after step 1, when using *rTorrent-PS*.
    It is *not* related to the ``tagged`` *field* in any way.

    They're just different ways to tag items, one of them visually in the *rTorrent-PS* UI.


Tag Episodes in rT-PS, Then Delete Their Whole Season
-----------------------------------------------------

The command below allows you to delete all items that belong to the same season of a TV series,
where single episodes were tagged as a stand-ins for that season.
The tagging can be done interactively in rTorrent-PS, using the ``.`` key.

.. code-block:: shell

    rtcontrol --from tagged -s* -qoname "/\\.S[0-9][0-9]E[0-9][0-9]\\./" \
        | sed -re 's/(.+\.[sS]..[eE])..\..+/\1/' | uniq | \
        | xargs -I# -d$'\n' rtcontrol '/^#/' --cull --yes -A dupes- loaded=+2w

The culling command call also protects any item younger than 2 weeks.


Using Tags or Flag Files to Control Item Processing
---------------------------------------------------

If you want to perform some actions on download items exactly once,
you can use tags or flag files to mark them as handled.
The basic pattern works like this:

.. code-block:: shell

    #! /usr/bin/env bash
    guard="handled"
    …

    rtcontrol --from-view complete -qohash tagged=\!$guard | \
    while read hash; do
        …

        # Mark item as handled
        rtcontrol -q --from-view $hash // --tag "$guard" --flush --yes --cron
    done

The ``--from-view $hash //`` is an efficient way to select a specific item by hash,
in case you wondered. ``hash=‹infohash›`` in contrast loads all items, then filters out just one.

A variant of this is to use a flag file in the download's directory –
such a file can be created and checked by simply poking the file system, which
can have advantages in some situations. To check for the existance
of that file, add a custom field to your ``config.py`` as follows::

    def is_synced(obj):
        "Check for .synced file."
        pathname = obj.path
        if pathname and os.path.isdir(pathname):
            return os.path.exists(os.path.join(pathname, '.synced'))
        else:
            return False if pathname else None

    yield engine.DynamicField(engine.untyped, "is_synced", "does download have a .synced flag file?",
        matcher=matching.BoolFilter, accessor=is_synced,
        formatter=lambda val: "SYNC" if val else "????" if val is None else "!SYN")

The condition ``is_synced=no`` is then used instead of the ``tagged`` one in the bash snippet above,
and setting the flag is a simple ``touch``. Add a ``rsync`` call to the ``while`` loop in the example
and you have a cron job that can be used to transfer completed items to another host *exactly once*.
Note that this only works for multi-file items, since a data directory is assumed –
supporting single-file items is left as an exercise for the reader.
See :ref:`CustomFields` for more details regarding custom fields.
