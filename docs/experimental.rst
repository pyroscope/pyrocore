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
