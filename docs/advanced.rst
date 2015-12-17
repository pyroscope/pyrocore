Advanced Features
=================

.. note::

    Using these features requires some knowledge in the area Linux, Bash,
    and Python beyond a novice level, but they enable you to customize
    your setup even further and handle very specific use-cases.


.. _CustomFields:

Defining Custom Fields
----------------------

.. include:: advanced-custom-fields.rst


.. _rtcontrol-exec:


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


Queue Manager
-------------

.. include:: advanced-queue.rst
