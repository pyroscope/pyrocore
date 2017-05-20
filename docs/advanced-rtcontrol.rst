.. _rtcontrol-spawn:

Executing OS commands
^^^^^^^^^^^^^^^^^^^^^

The ``--call`` and ``--spawn`` options can be used to call an OS level command
and feed it with data from the selected items. The argument to both options
is a template, i.e. you can have things like ``{{item.hash}}`` in them.

When using ``--call``, the command is passed to the shell for parsing
– with obvious implications regarding the quoting of arguments,
thus ``--call`` only makes sense if you need I/O redirection or similar shell features.

In contrast, the ``--spawn`` option splits its argument list according to shell rules *before*
expanding the template placeholders, and then calls the resulting sequence of command name
and arguments directly.
Consider ``--spawn 'echo "name: {{item.name}}"'`` vs. ``--spawn 'echo name: {{item.name}}'``
– the first form passes one argument to ``/bin/echo``, the second form two arguments.
Note that in both cases, spaces or shell meta characters contained in the item name are
of no relevance, since the argument list is split according to the template, *not* its expanded value.

To list all the fields available in the first five items, try this command:

.. code-block:: bash

    rtcontrol // -/5 --spawn "echo -e '\\n'{{item}}" | sed -re 's/, /,\n    /g'

Unlike ``--call``, where you can use shell syntax to call several commands, ``--spawn`` can be
passed several times for executing a sequence of commands. If any called command fails, the ``rtcontrol``
call is aborted with an error.


Copy Session Metafiles by Category
""""""""""""""""""""""""""""""""""

Here's a practical example for using ``--spawn``, it copies all your loaded metafiles
from the session directory into a folder structure categorized by the *ruTorrent* label.
Unlabelled items go to the ``_NOLABEL`` folder.

.. code-block:: bash

    target="/tmp/metafiles"
    rm -rf "$target"
    rtcontrol // \
        --spawn "mkdir -p \"$target/"'{{item.fetch(1) or \"_NOLABEL\"}}"' \
        --spawn 'cp {{item.sessionfile}} "'"$target"'/{{item.fetch(1) or \"_NOLABEL\"}}/{{item.name}}-{{item.hash[:7]}}.torrent"'

The copied metafiles themselves are renamed to the contained name of the item's data,
plus a small part of the infohash to make these names unique.

Replace the ``item.fetch(1)`` by ``item.‹fieldname›`` to categorize by other values, e.g. ``item.alias`` for ‘by tracker’.


.. _rtcontrol-exec:

Executing XMLRPC commands
^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to apply some custom XMLRPC commands against a set of download items,
the ``--exec`` option of ``rtcontrol`` allows you to do that. For global commands
not referring to specific items, see the next section about the ``rtxmlrpc`` tool.
Read through the following examples to understand how ``--exec`` works,
features are explained as they are used there.
Also make sure you understand basic things like :ref:`output-templates` beforehand,
it's assumed here that you do.

.. contents:: Examples for using ``--exec``
    :local:

.. note::

    Previously, the common way to handle use-cases covered by ``--exec`` was
    to pipe ``rtxmlrpc`` commands generated via templating into ``bash``.
    Don't do that anymore, it's quite inferior to using ``--exec``.


Repairing Stuck Items
"""""""""""""""""""""

Let's start with an easy example of using ``--exec``, where no templating is needed:

.. code-block:: bash

    rtcontrol --exec 'stop= ; close= ; f.multicall=,f.set_create_queued=0,f.set_resize_queued=0 ; check_hash=' \
              --from stopped -/1

This command simulates pressing ``^K^E^R`` in the curses UI (which cleans the state of stuck / damaged items)
and only affects the first stopped item.
Use different filter arguments after ``--exec`` to select other items.
Afterwards, use ``--start`` to start these items again.


Relocating Download Data
""""""""""""""""""""""""

The most simple variant of changing the download path is setting a new fixed location
for all selected items, as follows:

.. code-block:: bash

    rtcontrol --exec 'directory.set=/mnt/data/new/path' directory=/mnt/data/old/path

This replaces the location of items stored at ``/mnt/data/old/path`` with a new path.
But to be really useful, we'd want to shift *any* path under a given base directory
to a new location – the next command does this by using templating and calculating the
new path based on the old one:

.. code-block:: bash

    rtcontrol \
        --exec 'directory.set={{item.directory|subst("^/mnt/data/","/var/data/")}} ; >directory=' \
        directory=/mnt/data/\*

This selects any item stored under ``/mnt/data`` and relocates it to the new base directory
``/var/data``.
Fields of an item can be used via a ``item.‹field-name›`` reference.
Adding ``>directory=`` prints the new location to the console –
a semicolon with spaces on both sides delimits several commands, and the ``>`` prints the
result of a XMLRPC command. Also note that the ``d.`` prefix to download item commands is implied.


Making Shared Data Paths Unique
"""""""""""""""""""""""""""""""

Another example regarding data paths is this:

.. code-block:: bash

    rtcontrol --from stopped // --anneal dupes= --exec 'directory.set={{item.directory}}-{{item.hash}}'

That command ensures that items that would download into the same path get a unique name by appending the info hash,
and assumes those items weren't started yet (i.e. added via ``load.normal``).


Changing Announce URLs in Bulk
""""""""""""""""""""""""""""""

The next example replaces an active announce URL with a new one,
which is necessary after a domain or passkey change.
Compared to other methods like using ``sed`` on the files in your
session directory, this does not require a client restart, and is also safer
(the ``sed`` approach can easily make your session files unusable).
This disables all old announce URLs in group 0 using a ``t.multicall``,
and then adds a new one:

.. code-block:: bash

    rtcontrol \
        --exec 't.multicall=0,t.disable= ; tracker.insert=0,"http://new.example.com/announce" ; save_full_session=' \
        "tracker=http://old.example.com/announce"

The ``tracker.insert`` also shows that arguments to commands can be quoted.
