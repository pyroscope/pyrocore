Experimental Features
=====================

.. warning::

    The features described here are *unfinished* and in an alpha
    or beta stage.


Query Optimization
------------------

You can provide the ``--fast-query`` option of ``rtcontrol`` to set a level of optimization
to use when querying *rTorrent* for items. The default for that option is set via the
``fast_query`` config parameter, and is ``0`` if not changed. That means optimization is normally
off, and can be activated via ``-Q1``. It is recommended to keep it that way for now, and
use ``-Q1`` explicitly in scripts and other background processing to reduce the load they generate.
Only activating it in scripts usually means the filters used don't change that much, i.e. you can be pretty
sure the optimization does what you expect it to do.

Level 1 is less aggressive and safe by definition (i.e. produces correct results in all cases, unless there's a bug),
while ``-Q2`` is highly experimental and in some circumstances
likely produces results that are too small or empty.

Optimization works by giving a *pre-filter* condition to *rTorrent*, to reduce the overhead involved in
sending items over XMLRPC and processing them, only to be then discarded in the ``rtcontrol`` filter
machinery. That pre-filter evaluation needs features of *rTorrent-PS* 1.1 or later, and will produce
errors when used with anything else.

This goal of reducing the number of items sent to ``rtcontrol`` is best achieved if you put
a highly selective condition first in a series of conditions combined by ``AND``. For cron-type jobs,
this can often be achieved by looking at recent items only – older items should already be processed
by previous runs. Even a very lenient window like “last week” drastically reduces items
that need to be processed.

Consider this example:

.. code-block:: shell

    $ rtcontrol loaded=-6w is_ignored=0 -o- -v -Q0
    DEBUG    Matcher is: loaded=-6w is_ignored=no
    DEBUG    Got 131 items with 20 attributes …
    INFO     Filtered 13 out of 131 torrents.
    DEBUG    XMLRPC stats: 25 req, out 5.6 KiB [1.4 KiB max], in 104.9 KiB [101.5 KiB max], …
    INFO     Total time: 0.056 seconds.

    $ rtcontrol loaded=-6w is_ignored=0 -o- -v -Q1
    INFO     !!! pre-filter: greater=value=$d.custom=tm_loaded,value=1488920876
    DEBUG    Got 17 items with 20 attributes …
    INFO     Filtered 13 out of 131 torrents.
    DEBUG    XMLRPC stats: 25 req, out 5.7 KiB [1.5 KiB max], in 16.6 KiB [13.2 KiB max], …
    INFO     Total time: 0.028 seconds.

You can see that the 2nd command executes faster (the effect is larger with more overall items),
and only looks at 17 items to select the final 13 ones, while with ``-Q0`` all 131 items
need to be looked at, and thus transferred via XMLRPC. That means 105 KiB instead of only 16.6 KiB need
to be serialized, read, and parsed again.

Putting the right condition first is quite important, as you can see when the conditions are swapped
and the less selective one is used for the pre-filter:

.. code-block:: shell

    $ rtcontrol is_ignored=0 loaded=-6w -o- -v -Q1
    INFO     !!! pre-filter: equal=d.ignore_commands=,value=0
    DEBUG    Got 117 items with 20 attributes …

Be careful when mixing ``--anneal`` and ``--fast-query``, since most of the post-processing steps also look
at deselected items, and produce unexpected results if they are missing due to pre-filtering. Put another way,
always include ``-Q0`` when you use ``--anneal``, to be on the safe side.


Connecting via SSH
------------------

.. note:

    This is quite slow at the moment!

Starting with version 0.4.1, you can use URLs of the form

::

    scgi+ssh://[«user»@]«host»[:«port»]«/path/to/unix/domain/socket»

to connect securely to a remote rTorrent instance. For this to
work, the following preconditions have to be met:

  * the provided account has to have full permissions (``rwx``) on the given socket.
  * you have to use either public key authentication via ``authorized_keys``,
    or a SSH agent that holds your password.
  * the remote host needs to have the ``socat`` executable available (on
    Debian/Ubuntu, install the ``socat`` package).

You also need to extend the ``rtorrent.rc`` of the remote instance with
this snippet:

.. code-block:: shell

    # COMMAND: Return startup time (can be used to calculate uptime)
    method.insert = startup_time,value|const,$system.time=

For example, the following queries the remote instance ID using ``rtxmlrpc``:

.. code-block:: shell

    rtxmlrpc -v -Dscgi_url=scgi+ssh://user@example.com/var/torrent/.scgi_local session.name

This typically takes several seconds due to the necessary authentication.


.. _monitoring:

Using the Monitoring Web Service
--------------------------------

.. include:: advanced-monitoring.rst


Event Handling
--------------

**TODO**
– see `the old docs <https://github.com/pyroscope/pyroscope/tree/wiki/>`_ for anything not yet moved.


Queue Manager: Planned Features
-------------------------------

These aren't implemented yet…

``ExecCommand`` (planned)
^^^^^^^^^^^^^^^^^^^^^^^^^

**TODO** ``pyrocore.torrent.jobs:ExecCommand`` runs an external command
in a shell, i.e. it simply runs cron jobs. The reasons for not using
cron instead are these: 1. You can have all your rTorrent-related
background processing at one place, and the commands see the same
environment as ``pyrotorque``. 1. ``pyrotorque`` offers more flexible
scheduling, including the ability to run jobs at sub-minute intervals.

``RemoteWatch`` (planned)
^^^^^^^^^^^^^^^^^^^^^^^^^

**TODO** ``pyrocore.torrent.watch:RemoteWatch`` polls a (S)FTP source
for new ``.torrent`` files, creates a local copy, and loads that into
the client.

``ItemPoller`` (planned)
^^^^^^^^^^^^^^^^^^^^^^^^

**TODO** ``pyrocore.torrent.:`` maintains an updated copy of all
rTorrent items, as a service for the other jobs.

``ActionRule`` (planned)
^^^^^^^^^^^^^^^^^^^^^^^^

**TODO** ``pyrocore.torrent.filter:ActionRule`` is ``rtcontrol`` in form
of a house-keeping job, and using this is way more efficient than an
equivalent ``rtcontrol`` cron job; due to that, they can be run a lot
more frequently.

``TorrentMirror`` (planned)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**TODO** ``pyrocore.torrent.filter:TorrentMirror`` allows you to
transfer a torrent's data from the local client to other remote clients
using a specified tracker (at the start, a locally running "bttrack").
In a nutshell, it allows you to transfer any filtered item automatically
to a remote location via bittorrent.

``CompletionHandler`` (planned)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**TODO** ``pyrocore.torrent.:`` moves completed data to a target
directory, according to flexible rules.

``StatsArchiver`` (planned)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**TODO** ``pyrocore.torrent.:`` keeps a continuous archive of some
statistical values (like bandwidth) so they can later be rendered into
graphs.

See RtorrentMonitoring for more details.
