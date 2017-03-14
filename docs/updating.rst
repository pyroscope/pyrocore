Software Updates
================

.. include:: include-xmlrpc-dialects.rst


Making Backups
--------------

Since repairing broken files resulting from faulty updates usually is
either a lot of work or simply impossible, always **make a backup**.
Backups should be made when *either* PyroScope or rTorrent is changed to
a new release version or git revision.

These steps should make a copy of pretty much anything important:

 #. Copy your rTorrent session data (rTorrent needs to be running):

    .. code-block:: bash

        rtxmlrpc -q session.save
        tar cvfz /tmp/session-backup-$USER-$(date +'%Y-%m-%d').tgz \
            $(echo $(rtxmlrpc session.path)/ | tr -s / /)*.torrent

 #. Backup your current PyroScope virtualenv and configuration:

    .. code-block:: bash

        tar cvfz /tmp/pyroscope-backup-$USER-$(date +'%Y-%m-%d').tgz \
            ~/.pyroscope/ ~/.local/pyroscope/

 #. Depending on how you install rTorrent, make a copy of the rTorrent
    executable. Note that the ``rTorrent-PS`` build script installs into
    versioned directories, i.e. using that you don't have to worry if
    changing the rTorrent version ­— the old one is still available, and
    you can switch back easily.


.. _software-update:

Updating the Software
---------------------

**Before** adapting and extending your configuration to make use of new
features, you first have to update the software itself. How to do that
depends on the way you initially installed it, so follow **one** of the
following sections, depending on whether you did a
:ref:`release installation <software-update-from-pypi>`
or one :ref:`from source <software-update-from-source>`.

.. _software-update-from-pypi:


How to Do a Release Version Software Update
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Remember to read the **migration instructions** further below, and the `changelog`_,
**BEFORE** installing any new version.

Then to **update** an existing installation, use this command **if** you
used the instructions on the InstallReleaseVersion page:

.. code-block:: bash

    sudo easy_install --prefix /usr/local -U pyrocore

Now **skip** the next section describing a source installation upgrade,
and go to the configuration update further below.


.. _software-update-from-source:

How to Update a Source Installation to the Newest Code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**BEFORE** any update, remember to read the **migration instructions**
further below, the `changelog`_ and the `list of commits`_.

Then to **update** an existing installation, use these commands:

.. code-block:: bash

    cd ~/.local/pyroscope
    ./update-to-head.sh


.. _config-update:

Updating Your Configuration
---------------------------

After you installed a new version of the software, you can easily check
whether the default configuration files changed by calling the
``pyroadmin --create-config`` command. Since this will never overwrite
existing configuration files, the files ``config.ini.default`` and
``config.py.default`` will be created instead.

You can then use the ``diff`` tool to check for the differences between
your current configuration and the new default one, and add any changes
you want to adopt. Also note that sections of the configuration you
leave out, and keys that you do not overwrite, are automatically taken
from the defaults, which greatly simplifies any update — so having a
minimal configuration with just the changes and additions you actually
want is recommended.

And remember to **always read the `changelog`_**!


Migrating to Version 0.4.1
^^^^^^^^^^^^^^^^^^^^^^^^^^

There is a new dependency on the ``pyrobase`` package, and for **release
version installations**, it will be managed transparently — you have
nothing to worry about, just follow the updating instructions from
InstallReleaseVersion, and then see below for the required steps after
updating.

On the other hand, if you have an **installation from source**, it's
important that you add the new dependency *also* from source, because
otherwise your installation will break during further development (since
then, you'd remain on the *released* version of ``pyrobase``). So, call
these commands (assuming the standard installation paths):

.. code-block:: bash

    cd ~/.local/pyroscope
    source bin/activate
    svn update
    git clone git://github.com/pyroscope/pyrobase.git pyrobase
    ( cd pyrocore && source bootstrap.sh )

In addition, follow these steps: 1. You **must** add the new
``startup_time`` command, and you *should* add the ``cull`` command (see
*Extending your ``.rtorrent.rc``* on the UserConfiguration page). 1.
Call ``pyroadmin --create-config`` to add the new builtin `Tempita
templates <OutputTemplates.md>`_ to your configuration. 1. To get bash
completion for the PyroScope commands, see the instructions on the
BashCompletion page.


Migrating to Version 0.4.2
^^^^^^^^^^^^^^^^^^^^^^^^^^

Release 0.4.2 not only contains some additions to the PyroScope
commands, but also offers you to run an `extended rTorrent
distribution <RtorrentExtended.md>`_ with many user interface and
command improvements. You need to decide whether you want to run that
version, it involves compiling your own rTorrent executable, but there
is a build script that mostly automates the process.

But first, to upgrade your existing installation, follow these steps: 1.
For people that run a source code installation. use the new
``update-to-head.sh`` script as outlined further up on this page. 1.
Call ``pyroadmin --create-config`` to update the ``.default``
configuration examples, and also to create the new ``.rtorrent.rc``
include (see next step). 1. Read the section *Extending your
``.rtorrent.rc``* on the UserConfiguration page again! There is a new
standard configuration include, which greatly simplifies integrating
additional PyroScope settings into your main configuration. Add that
include as shown there, and take care to remove anything from the main
``.rtorrent.rc`` that's already added by the include, else you get error
messages on startup, or worse, inconsistent behaviour. 1. Restart
rTorrent and try to do a search using ``^X s=x264`` or another keyword
you expect some hits on. If that works, you can be pretty sure
everything's OK

The new stable version 0.8.9 of rTorrent is now supported by this
release, see RtXmlRpcMigration for details.


Migrating to Version 0.5.1 (UNRELEASED)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``0.5.1`` release adds a queue manager,
watching a directory tree for loading metafiles,
and removes support for ancient versions of *Python* and *rTorrent*.

To upgrade your existing installation, follow these steps:

#. For people that run a source code installation. use the ``update-to-head.sh``
   script as usual, outlined further up on this page.
#. Call ``pyroadmin --create-config`` to update the ``.default`` configuration
   examples.
#. You also **MUST** change the ``import`` command in your ``rtorrent.rc``
   that loads the PyroScope configuration include:

   .. code-block:: ini

      # Remove the ".default" if you want to change something (else your changes
      # get over-written on update, when you put them into ``*.default`` files).
      import = ~/.pyroscope/rtorrent-pyro.rc.default

#. Read the :ref:`QueueManager` section if you plan to use item queueing
   and/or the tree watch feature; both are inactive by default and need to be
   enabled. You also need to add the new ``pyro_watchdog`` schedule into your
   configuration, as shown in the :doc:`setup`.

.. _`changelog`: https://github.com/pyroscope/pyrocore/blob/master/debian/changelog
.. _`list of commits`: https://github.com/pyroscope/pyrocore/commits/master
