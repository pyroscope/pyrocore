Advanced Features
=================

.. note::

    Using these features requires some knowledge in the area Linux, Bash,
    and Python beyond a novice level, but they enable you to customize
    your setup even further and handle very specific use-cases.


Modifying and extending your configuration via 'config.py'
----------------------------------------------------------

As mentioned in the :doc:`setup`, the ``config.py`` script can be used to add
custom logic to your setup. The most common use for this file is adding
custom fields, described in the next section.


.. _CustomFields:

Defining Custom Fields
----------------------

.. include:: advanced-custom-fields.rst


.. _rtcontrol-exec:


Executing OS commands with rtcontrol
------------------------------------

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

Unlike ``--call``, where you can use shell syntax to call several commands, ``--spawn`` can be
passed several times for executing a sequence of commands. If any called command fails, the ``rtcontrol``
call is aborted with an error.


Executing XMLRPC commands with rtcontrol
----------------------------------------

If you want to apply some custom XMLRPC commands against a set of download items,
the ``--exec`` option of ``rtcontrol`` allows you to do that. For global commands
not referring to specific items, see the next section about the ``rtxmlrpc`` tool.

Let's start with an easy and typical example of using ``--exec``::

    rtcontrol --exec directory.set=/mnt/data/new/path directory=/mnt/data/old/path

This simply replaces the location of items stored at ``/mnt/data/old/path`` with a new path.
But to be really useful, we'd want to shift *any* path under a given base directory
to a new location – the next command does this by using templating and calculating the
new path based on the old one::

    rtcontrol \
        --exec 'directory.set={{item.directory|subst("^/mnt/data/","/var/data/")}} ; >directory=' \
        directory=/mnt/data/\*

This selects any item stored under ``/mnt/data`` and relocates it to the new base directory
``/var/data``. Adding ``>directory=`` prints the new location to the console –
a semicolon with spaces on both sides delimits several commands, and the ``>`` prints the
result of a XMLRPC command. Also note that the ``d.`` prefix to download item commands is implied.

The next example replaces an active announce URL with a new one,
which is necessary after a domain or passkey change.
This disables all old announce URLs in group 0 using a ``t.multicall``,
and then adds a new one::

    rtcontrol \
        --exec 't.multicall=0,t.disable= ; tracker.insert=0,"http://foobaz.example.com/announce" ; save_full_session=' \
        "tracker=http://foobar.example.com/announce"

The ``tracker.insert`` also shows that arguments to commands can be quoted.

.. note::

    Previously, the common way to handle use-cases covered by ``--exec`` was
    to pipe ``rtxmlrpc`` commands generated via templating into ``bash``.
    Don't do that anymore, it's quite inferior to using ``--exec``.


.. _RtXmlRpcExamples:

Using rtxmlrpc
--------------

.. include:: advanced-rtxmlrpc.rst


.. _QueueManager:

rTorrent Queue Manager
----------------------

.. include:: advanced-queue.rst
