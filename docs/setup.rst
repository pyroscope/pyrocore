Configuration Guide
===================


Introduction
------------

After you installed the software as described in the previous chapter, you
need to add personal configuration that is loaded from the directory
``~/.pyroscope`` containing the files ``config.ini`` and ``config.py``.
A default set can be automatically created for you, see below for
details.

For simple setups, you only need to edit the plain text file
``config.ini``. The script ``config.py`` allows much more detailed
control over complex setups, at the price of you knowing at least the
basics of the Python programming language. See :doc:`advanced` for that.

.. note::

    For a fresh installation of this software in addition to an *existing*
    rTorrent one, you will also need to back-fill some data that your already
    running rTorrent instance is missing otherwise. If you skip this step, item
    filtering in ``rtcontrol`` and other tools will *not* work correctly for
    existing items. More on that below.

In summary, you'll perform these steps, explained in the sections that follow:

 #. Create a directory with the default configuration.

 #. Edit ``~/.pyroscope/config.ini`` to adapt it to your needs, e.g. add tracker aliases.

 #. Modify your ``~/.rtorrent.rc`` to integrate necessary settings.

 #. Back-fill some data into the *rTorrent* session.

.. include:: include-contacts.rst


Creating a set of default configuration files
---------------------------------------------

To create your own configuration, the best way is to start from the
default files that are part of your PyroScope installation. To create
them at the default location ``~/.pyroscope``, simply call this command:

.. code-block:: bash

    pyroadmin --create-config

Note that you can delete any defult setting from ``config.ini`` that you don't want changed.
These defaults are *always* loaded before your own settings, from a copy the software keeps and updates.

Deleting unchanged defaults has the advantage that on software updates,
you'll automatically get the newer version of settings, as soon as they're
updated. The created ``config.ini.default`` file is just for reference,
and will be overwritten on updates.

If you need several distinct configuration sets, just add the
``--config-dir`` option to commands like so:

.. code-block:: bash

    pyroadmin --create-config --config-dir ~/rtorrent/special/.pyroscope

To view your loaded configuration with all the system defaults added,
use this (again, the ``--config-dir`` option allows non-default
configuration locations):

.. code-block:: bash

    pyroadmin --dump-config

To start over with a pristine set of configuration files, and remove
any stale ones, add the ``--remove-all-rc-files`` option:

.. code-block:: bash

    pyroadmin --remove-all-rc-files --create-config

Be aware that this *really* removes **any** ``*.rc`` and ``*.rc.default``
file in ``~/.pyroscope`` and its subfolder ``rtorrent.d``, before writing
a new set of files.

.. note::

    Each *PyroScope* configuration file is accompanied by a matching ``*.default`` file
    that contains the system defaults at the time you last called the
    ``pyroadmin --create-config`` command. These are over-written on repeated
    calls (unlike the real config files), and are for informational purposes only.

    For the *rTorrent* configuration files (``rtorrent-pyro.rc[.default]`` and
    files in ``rtorrent.d``), the rules are different. These files change frequently,
    so the ``*.default`` versions are loaded usually, and you get an up-to-date version
    on a *rTorrent* restart.

    You can ignore specific files in ``rtorrent.d`` if they don't fit or you want to
    provide your own version under *another* name.
    See the files themselves for instructions.


.. _config-ini:

Setting values in 'config.ini'
------------------------------

The main configuration file consists of sections, led by a ``[section]``
header and followed by ``name: value`` entries; ``name = value`` is also
accepted. Longer values can be broken into several lines and the
continuation lines must be indented (start with a space). Note that
leading whitespace is removed from values.

Lines beginning with a semicolon (``;``), a hash mark (``#``), or the
letters ``REM`` (uppercase or lowercase) will be ignored and can be used
for comments. You cannot append a comment to an option line, a comment
**MUST** start at the beginning of a line!

As an example, this is a very minimal configuration file:

.. code-block:: ini

    # PyroScope configuration file

    [GLOBAL]
    # Note that the "config_dir" value is provided by the system!
    config_script = %(config_dir)s/config.py
    rtorrent_rc = ~/.rtorrent.rc

    [ANNOUNCE]
    # Add alias names for announce URLs to this section; those aliases are used
    # at many places, e.g. by the "mktor" tool

    # Public trackers
    PBT     = http://tracker.publicbt.com:80/announce
              udp://tracker.publicbt.com:80/announce
    OBT     = http://tracker.openbittorrent.com:80/announce
              udp://tracker.openbittorrent.com:80/announce
    Debian  = http://bttracker.debian.org:6969/announce

.. note::

    *For advanced users:* Values can contain format strings of the form
    ``%(name)s`` which refer to other values in the same section, or values
    in the ``[DEFAULT]`` section.


Extending your '.rtorrent.rc'
-----------------------------

You need either a ``network.scgi.open_local`` or ``network.scgi.open_port`` specification in your
rTorrent configuration, else XMLRPC cannot work;
``network.scgi.open_local`` is preferable since more secure.
Furthermore, you need to provide the path to a session directory via ``session.path``.
See the *rTorrent* documentation for details.

.. note::

    Using ``network.scgi.open_port`` means *any* user on the machine you run *rTorrent* on can
    execute *arbitrary* commands with the permission of the *rTorrent* runtime user.
    Most people don't realize that, now you do! Also, **never** use any other address than
    ``127.0.0.1`` with it.

For the ``loaded`` and ``completed`` fields to work, as well as the
``started``, ``leechtime`` and ``seedtime`` ones, you also have to add
these commands (note that most settings actually reside in an
`included file <https://github.com/pyroscope/pyrocore/blob/master/src/pyrocore/data/config/rtorrent-pyro.rc>`_):

.. code-block:: ini

    #
    # PyroScope SETTINGS
    #

    # Set "pyro.extended" to 1 to activate rTorrent-PS features!
    # LEAVE THIS AT 0 IF YOU RUN A VANILLA rTorrent!
    method.insert = pyro.extended, value|const, 0

    # Set "pyro.bin_dir" to the "bin" directory where you installed the pyrocore tools!
    # Make sure you end it with a "/"; if this is left empty, then the shell's path is searched.
    method.insert = pyro.bin_dir, string|const,

    # Remove the ".default" if you want to change something (else your changes
    # get over-written on update, when you put them into ``*.default`` files).
    import = ~/.pyroscope/rtorrent-pyro.rc.default

    # TORQUE: Daemon watchdog schedule
    # Must be activated by touching the "~/.pyroscope/run/pyrotorque" file!
    # Set the second argument to "-v" or "-q" to change log verbosity.
    schedule = pyro_watchdog,30,300,"pyro.watchdog=~/.pyroscope,"

See this
`rtorrent.rc <https://github.com/pyroscope/pimp-my-box/blob/master/roles/rtorrent-ps/templates/rtorrent/rtorrent.rc>`_
and the
`_rtlocal.rc <https://github.com/pyroscope/pimp-my-box/blob/master/roles/rtorrent-ps/templates/rtorrent/_rtlocal.rc>`_
file it includes for a complete example,
including some view changes regarding sort order made possible by the additional custom fields.

.. note::

    Remember to restart *rTorrent* for the new configuration to take effect.
    If you also installed the `rtorrent-ps`_ distribution of *rTorrent*,
    do not forget to activate the extended features available with it,
    by setting ``pyro.extended`` to ``1`` in the above configuration.


.. _backfill-data:

Adding Missing Data to Your rTorrent Session
--------------------------------------------

Now that you have the additional configuration, *newly loaded* items will get the correct values set
– but existing items are still missing them, and so those items will *not* always be filtered correctly.
If you just started with a fresh install and have no items added to rTorrent yet, you can ignore this section.

To add the missing data, call these commands:

.. code-block:: bash

    # Make a full, current backup of the session data
    rtxmlrpc -q session.save
    tar cvfz ~/session-backup-$(date +'%Y-%m-%d').tgz \
        $(echo $(rtxmlrpc session.path)/ | tr -s / /)*.torrent*

    # Set missing "loaded" times to that of the .torrent file
    rtcontrol '!*"*' loaded=0 -q -sname -o 'echo "$(name)s"\ntest -f "$(metafile)s" && rtxmlrpc -q d.custom.set $(hash)s tm_loaded \$(\
        ls -l --time-style "+%%s" "$(metafile)s" \
        | cut -f6 -d" ")\nrtxmlrpc -q d.save_full_session $(hash)s' | bash

    # Set missing "completed" times to that of the data file or directory
    rtcontrol '!*"*' completed=0 done=100 path=\! is_ghost=no -q -sname -o 'echo "$(name)s"\ntest -e "$(realpath)s" && rtxmlrpc -q d.custom.set $(hash)s tm_completed \$(\
        ls -ld --time-style "+%%s" "$(realpath)s" \
        | cut -f6 -d" ")\nrtxmlrpc -q d.save_full_session $(hash)s' | bash

It's safe to call them repeatedly, since existing values are kept unchanged.

To check, use the command ``rtcontrol completed=-1d -scompleted`` which should now
show your completed downloads of the last 24 hours, in order.


.. _`rtorrent-ps`: https://github.com/pyroscope/rtorrent-ps
