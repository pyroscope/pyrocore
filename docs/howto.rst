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

.. _multi-instance:

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

Alternatively, you can also set the ``scgi_url`` value directly, like in this example:

.. code-block:: shell

    rtxmlrpc -D scgi_url=scgi:///var/run/rtorrent/instance01 session.name


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


.. _host-move:

Host Migration of Data & State
------------------------------

If you want to move items and their data to another host,
there are endless ways to do that,
with different grades of difficulty
and how much state is carried over.

The way described here allows you to move items
per directory they are stored in,
which fits nicely with typical hierarchies created by completion moving.

In consequence, you can split the existing data if you need to, or just move a subset.
If you vary the commands, you can adapt this to your needs,
e.g. move all items at once.


.. important::

    You need *git head* or v0.6.1 for this.

This first command lists all the unique storage paths you have,
and how many items they hold:

.. code-block:: shell

    # List all the unique storage paths containing download items
    rtcontrol path='!' -qo realpath.pathdir | sort | uniq -c \
        | awk -F' ' '{ print $0; sum += $1} END { printf "%7d ITEMS TOTAL\n", sum; }'

Always call that initially to check if the output makes sense to you
– otherwise you likely have some inconsistencies in your setup
that need to be fixed first.

The next series of commands creates a hidden ``.metadata`` folder
in each storage path, and copies the session metafiles and
other state of contained items into that.
The last command lists the results.

.. code-block:: shell

    alias foreachpath='rtcontrol path=! -qo realpath.pathdir -0 | sort -uz | xargs -0I#'

    # Create ".metadata" hidden folders in those directories
    foreachpath mkdir -p "#/.metadata"

    # Save state and all metafiles per path
    foreachpath rm -f "#/.metadata/_all-items"
    foreachpath rtcontrol realpath='/^#(/[^/]+|)$/' \
        --call 'echo "{{item.hash}}:{{item.name}}:{{item.realpath | pathbase}}" \
        >>"#/.metadata/_all-items"'
    for i in '' .rtorrent .libtorrent_resume; do
        echo "~~~ session '*.torrent$i'"
        foreachpath rtcontrol realpath='/^#(/[^/]+|)$/' \
            --spawn 'cp {{item.sessionfile}}'$i' "#/.metadata/{{item.name}}-{{item.hash}}.torrent'$i'"'
    done

    # List the saved metadata files
    foreachpath find "#/.metadata" | sort | less

To use the generated ``_all-items`` files, this is how you can read them:

.. code-block:: shell

    while IFS=':' read h n f; do
        echo -e "$h\\n  name = $n\\n  file = $f"
    done <.metadata/_all-items

While the name and the filename are usually identical,
they *can* differ if you used
`d.directory_base.set <https://rtorrent-docs.readthedocs.io/en/latest/cmd-ref.html#term-d-directory-base-set>`_
on an item.

The best way to migrate the data is using ``rsync``,
especially since it allows incremental updates,
and setting bandwith limits.
Change ``OTHERHOST`` to the domain name or ``~/.ssh/config`` alias of the target host.

This command replicates all storage paths to the remote host,
keeping the file system paths the same
(that is not required though, prefix or replace the rightmost ``#`` at will).

.. code-block:: shell

    foreachpath rsync -avhP --stats --times --bwlimit=42000 "#/" "OTHERHOST:#"

Add ``echo`` before ``rsync`` to just list the commands,
e.g. to only sync one of the directories.

.. tip:: **Splitting items into several rTorrent instances**

    If your leave out the ``rsync`` parts and replace them with moving
    data to different instance's data directories,
    you can nicely split up large volumes of data by the groups
    your completion moving or storage path presets created anyway.

    Loading the items then does not happen on a target host,
    but into the target instances.
    See :ref:`multi-instance` on how to select the targets
    when you run them under just one user account.


**TODO** load items into target rTorrent instance


Finally, if everyhting looks OK on the target,
you might remove the source data:

.. code-block:: shell

    rm -f /tmp/rt-cleanup-$USER.sh
    foreachpath echo rm -rf \""#/"\" >>/tmp/rt-cleanup-$USER.sh
    foreachpath rtcontrol realpath='/^#(/[^/]+|)$/' --cull
    bash -x /tmp/rt-cleanup-$USER.sh  # optionally delete left-overs


Tag Episodes in rT-PS, Then Delete Their Whole Season
-----------------------------------------------------

The command below allows you to delete all items that belong to the same season of a TV series,
where single episodes were tagged as a stand-in for their season.
The tagging can be done interactively in rTorrent-PS, using the ``.`` key.

.. code-block:: shell

    rtcontrol --from tagged -s* -qoname "/\\.S[0-9][0-9]E[0-9][0-9]\\./" \
        | sed -re 's/(.+\.[sS]..[eE])..\..+/\1/' | uniq | \
        | xargs -I# -d$'\n' rtcontrol '/^#/' loaded=+2w -A dupes- --cull --yes

The culling command call also protects any item younger than 2 weeks,
and excludes any dupes that were not fully caught by the selection.
Replace the ``--cull --yes`` with ``-V`` to preview what would be deleted.


.. _guard-tags:

Using Tags or Flag Files to Control Item Processing
---------------------------------------------------

If you want to perform some actions on download items exactly once,
you can use tags or flag files to mark them as handled.
The basic pattern works like this:

.. code-block:: shell

    #! /usr/bin/env bash
    guard="handled"
    …

    rtcontrol --from-view complete -qohash --anneal unique tagged=\!$guard | \
    while read hash; do
        …

        # Mark item as handled
        rtcontrol -q --from-view $hash // --tag "$guard" --flush --yes --cron
    done

The ``--from-view $hash //`` is an efficient way to select a specific item by hash,
in case you wondered. ``hash=‹infohash›`` in contrast loads all items, then filters out just one.
And ``--anneal unique`` prevents items duplicated by name to be processed several times
(by ignoring the duplicates).

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

Note that the flag file code as presented only works for multi-file items, since a data directory is assumed –
supporting single-file items is left as an exercise for the reader.
See :ref:`CustomFields` for more details regarding custom fields.



.. _info-source:

Metafile Creation with `info.source` from Configuration
-------------------------------------------------------

Say you want to add the ``info.source`` field for various trackers to new torrents,
during their creation in a script.

If the script takes the *alias* of the target tracker as an input,
this how-to shows a way to fetch the right source field from configuration (``config.ini``).
As a result, the script is portable between different setups and users.

The first step is to define a command for each affected tracker that adds its custom data
(you could set more than just the source field here).
We do so in a *new* section named ``COMMANDS``.

.. code-block:: ini

    [COMMANDS]
    custom_meta_tec = chtor -q --set info.source='tracker.example.com'

    [ANNOUNCE]
    TEC     = https://tracker.example.com/announce.php
              https://tracker.example.com/announce.php?passkey=12300000000000000000000000000456

You can immediately check your settings using ``pyroadmin``:

.. code-block:: console

    $ pyroadmin -qo commands
    {'custom_meta_tec': "chtor -q --set info.source='tracker.example.com'"}
    $ pyroadmin -qo commands.custom_meta_tec
    chtor -q --set info.source='tracker.example.com'

As you can see, we're now able to look up the metafile manipulation command via the tracker alias.
That is used in the following shell snippet to call this command on the created metafile.

.. code-block:: sh

    eval $(pyroadmin -qo commands.custom_meta_$tracker=:) "$metafile"

Since we build the command dynamically, the bash ``eval`` builtin is used.
The nested ``pyroadmin`` call does the lookup of the first command part,
and returns ``:`` in case there is no command set for a specific tracker
(that is what the ``=:`` is for).
``:`` is a builtin command documented as *do nothing, successfully*
– i.e. if we have no command configured, the whole ``eval`` construct is a no-op.

Here's a trace of what happens for known and unknown aliases:

.. code-block:: console

    $ ( tracker=tec; metafile=foo.torrent; set -x ; \
        eval $(pyroadmin -qo commands.custom_meta_$tracker=:) $metafile )
    ++ pyroadmin -qo commands.custom_meta_tec=:
    + eval chtor -q --set 'info.source='\''tracker.example.com'\''' foo.torrent
    ++ chtor -q --set info.source=tracker.example.com foo.torrent
    $ ( tracker=unknown; metafile=foo.torrent; set -x ; \
        eval $(pyroadmin -qo commands.custom_meta_$tracker=:) $metafile )
    ++ pyroadmin -qo commands.custom_meta_unknown=:
    + eval : foo.torrent
    ++ : foo.torrent


Moving All Untied Metafiles Out of a Watch Tree
-----------------------------------------------

Sometimes when rTorrent starts, you see the following message, possibly repeated a lot:

    Could not create download: Info hash already used by another torrent.

That is caused by metafiles with the same infohash but from different sources
(in different files), that are somehow left over in a watch directory.
A typical variant is when a watch file clashes
with a previously untied item now loaded via the session.

To fix it for good, you can check all metafiles
found in a watch tree if they're still tied to an item in rTorrent,
or else move them away, like this:

.. code-block:: sh

    ( command cd "/var/torrent/watch" && find . -type f -name "*.torrent" | \
    while read metafile; do
        rtcontrol -qo- metafile='*/'$(tr -c '\n\-._/a-zA-Z0-9' '*' <<<"${metafile#*/}"); RC=$?
        if test $RC -eq 44; then
            target="/var/torrent/backups/untied/$(dirname "$metafile")"
            echo -e "\nMoving '$metafile'..."
            mkdir -p "$target"
            mv -n "$metafile" "$target"
            continue
        elif test $RC -ne 0; then
            break
        fi
        echo -n '.'
    done )

The loop is not optimized for speed, but then you don't need to call this very often.

On a related note, to list all the metafiles
that an item is still tied to but that doesn't exist anymore,
use this command:

.. code-block:: sh

    rtcontrol -q 'metafile=!' --call \
        'test -f "{{ item.metafile }}" || echo "{{ item.metafile }}"'

To make the untied state visible in the client, call this:

.. code-block:: sh

    rtcontrol -q 'metafile=!' --call \
        'test -f "{{ item.metafile }}" || rtxmlrpc -q d.delete_tied "{{ item.hash }}"'
