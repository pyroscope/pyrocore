Experimental Features
=====================

.. earning::

    The features described here are *unfinished* and in an alpha
    or beta stage.


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
    system.method.insert = startup_time,value,$system.time=

For example, the following queries the remote instance ID using ``rtxmlrpc``:

.. code-block:: shell

    rtxmlrpc -v -Dscgi_url=scgi+ssh://user@example.com/~/rtorrent/.scgi_local get_name

This typically takes several seconds due to the necessary authentication.


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
