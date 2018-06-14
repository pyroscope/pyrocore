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

 #. Copy your *rTorrent* session data and configuration (``rtorrent`` needs to be running):

    .. code-block:: bash

        rtxmlrpc -q session.save
        tar cvfz /tmp/instance-backup-$USER-$(date +'%Y-%m-%d').tgz \
            $(echo $(rtxmlrpc session.path)/ | tr -s / /)*.torrent \
            ~/rtorrent/*.rc ~/rtorrent/rtorrent.d ~/rtorrent/start

 #. Backup your current *PyroScope* virtualenv and configuration
    (use ``~/lib`` instead of ``~/.local`` for installations before ``0.5.1``):

    .. code-block:: bash

        tar cvfz /tmp/pyroscope-backup-$USER-$(date +'%Y-%m-%d').tgz \
            ~/.pyroscope/ ~/.local/pyroscope/

 #. Depending on how you installed *rTorrent*, make a copy of the ``rtorrent``
    executable and ``libtorrent*.so*``.
    Note that the `rTorrent-PS`_ build script installs into versioned directories,
    i.e. using that you don't have to worry if changing to a new *rTorrent* version
    ­— the old one is still available, and you can switch back easily.


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

Then to **update** an existing installation, use these commands
(but note the ``0.5.1`` update is different, see below):

.. code-block:: bash

    cd ~/.local/pyroscope
    bin/pip install -U "pyrocore[templating]"
    ln -nfs $(egrep -l '(from.pyrocore.scripts|entry_point.*pyrocore.*console_scripts)' $PWD/bin/*) ~/bin

If you used ``pip install --user -U pyrocore`` without creating a virtualenv, just repeat that command.

Now **skip** the next section describing a source installation upgrade,
and go to the :ref:`configuration update <config-update>` further below.


.. _software-update-from-source:

How to Update a Source Installation to the Newest Code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**BEFORE** any update, remember to read the **migration instructions**
further below, the `changelog`_ and the `list of commits`_.

Then to **update** an existing installation, use this command:

.. code-block:: bash

    ~/.local/pyroscope/update-to-head.sh

Continue with any tasks regarding configuration changes from the next section.


.. _config-update:

Updating Your Configuration
---------------------------

After you installed a new version of the software,
you have to check for necessary changes to the default configuration,
after calling the ``pyroadmin --create-config`` or the ``update-to-head.sh`` command.

Note that only the ``*.default`` files (``config.ini.default``, ``config.py.default``,
and so on) will be overwritten, they are a literal copy of
the defaults packaged into the software, and are there for informational purposes only.
You can then use the ``diff`` tool to check for the differences between
your current configuration and the new default one, and add any changes
you want to adopt.

Also note that sections of the configuration you
leave out, and keys that you do not overwrite, are automatically taken
from the defaults, which greatly simplifies any update.
That is the reason why it is recommended to have a minimal configuration
with just your customizations, in addition to the defaults.

The file ``~/.pyroscope/rtorrent-pyro.rc.default``,
and those contained in ``~/.pyroscope/rtorrent.d``, are a different story.
They change quite often, and since there is no merging of ``*.rc.default`` with
``*.rc`` files, the default ones are normally used.
You can still disable those default files one by one using the ``rtorrent.d/.rcignore`` file,
in order to provide your own versions or simply disable certain features.
That is way better than switching altogether to ``*.rc`` files,
again for the reason updates become way more painless.
See the comments at the start of files in ``rtorrent.d`` for details.

And remember to **always** read the `changelog`_!


Migrating to Version 0.5.x
^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``0.5.x`` release line adds a queue manager,
watching a directory tree for loading metafiles,
and removes support for ancient versions of *Python* and *rTorrent*.
More details on the contained changes can be found at `GitHub releases`_ and the `changelog`_.
Install at least version ``0.5.3``, which has a few important fixes.

To upgrade your existing installation, follow these steps:

#. For people that run a source code installation, just use the ``update-to-head.sh``
   script as described in :ref:`Installing from GitHub <install-from-github>`.
   When your old installation is still in ``~/lib``, you'll be presented with
   the necessary commands to move to ``~/.local`` *after* calling
   ``~/lib/pyroscope/update-to-head.sh``.
   Since all the documentation now points to ``~/.local`` paths, you should switch over.

   For PyPI installs, just do a :ref:`fresh install <install-from-pypi>` to the new location
   at ``~/.local``.
#. Call ``pyroadmin --create-config`` to update the ``.default`` configuration
   examples, and create the new ``rtorrent.d`` directory.
#. In your *rTorrent* instance, `update the start script`_ (and save a copy of the old one before that).
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
#. Remember to restart *rTorrent* after any configuration changes.

When you have a rather aged configuration, also consider switching to the new
set of configuration files as found in the ``pimp-by-box`` project, that use
the new command names through-out and are thus way more future-proof.

There is an easy to use ``make-rtorrent-config.sh`` script, see
`rTorrent Configuration`_ on how to use it.
At the same time, `update the start script`_.
Note that these configuration files also work with a plain vanilla *rTorrent* version,
you do **not** need *rTorrent-PS* for them to work.

In any case, **make a backup** of your configuration and scripts,
as mentioned at the start of this chapter. After creating the new configuration,
merge in what's missing from your old configuration, but `migrate to the new syntax`_ first.
For adding your custom settings, you can use your own files in the ``~/rtorrent/rtorrent.d`` directory.


Migrating to Version 0.6.1 (UNRELEASED)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``0.6.x`` release line adds support for the new *canvas v2* feature of `rTorrent-PS 1.1`
in the configuration files.

Notable ``rtcontrol`` changes are a new timestamp field ``last_xfer``,
useful in sorting views and selecting items for deletion that are not in high demand.
The ``--alter-view`` option allows manipulating filter results in views
incrementally (using several command calls).
More details on the contained changes can be found at `GitHub releases`_ and the `changelog`_.

When you have a rather aged configuration, also consider switching to the new
set of configuration files as found in the ``pimp-by-box`` project, that use
the new command names through-out and are thus way more future-proof.
More on that in the upgrade steps right below, and the next paragraph.

Note that v0.9.7 of `rTorrent` finally does away with many of those old comamnds.
Read the section on 0.5.x, right above this one,
regarding the ``make-rtorrent-config.sh`` script, which provides compatible config files
covering most of what people typically need.

To upgrade your existing installation, follow these steps:

#. For people that run a source code installation, just use the ``update-to-head.sh``
   script as described in :ref:`Installing from GitHub <install-from-github>`.
#. Call ``pyroadmin --create-config`` to update the ``.default`` configuration.
#. You also **MUST** change the `pyrocore` config snippet in your ``rtorrent.rc``,
   and add the ``system.has`` fallback for vanilla `rTorrent` and pre-1.1 `rTorrent-PS`.

   .. code-block:: ini

      # `system.has` polyfill (the "false=" silences the `catch` command, in rTorrent-PS)
      catch = {"false=", "method.redirect=system.has,false"}

   Re-read the :doc:`setup`, which has more information generally, and extensions
   to not only ``rtorrent.rc`` but also the minimal ``config.ini``.

   Specifically if you use `rTorrent-PS` 1.1 with the new *canvas v2* feature,
   you then *MUST* update the files in ``~/rtorrent/rtorrent.d/``,
   because there's lots of relevant changes.

   The ``make-rtorrent-config.sh`` does that, but overrites any changes you
   might have made. The best way to handle that is to put your config into git
   *before* calling the script a second time.
   That way, diffs get easy and nothing can be lost
   – you ‘just’ need to do the merging.

   Read `rTorrent Configuration`_ about how to avoid changing standard files
   by using ``_rtlocal.rc`` instead,
   and/or your own added files in ``rtorrent.d``.
   Then you have a way more painless updating experience – next time, anyway.

#. Remember to restart *rTorrent* after any configuration changes.

In any case, **make a backup** of your configuration and scripts,
as mentioned at the start of this chapter, *before* performing any update steps.
By the way, putting stuff into git, and also committing it, counts as a backup.

.. _`rTorrent Configuration`: https://rtorrent-ps.readthedocs.io/en/latest/install.html#make-rtorrent-config
.. _`rTorrent-PS`: https://github.com/pyroscope/rtorrent-ps#rtorrent-ps
.. _`migrate to the new syntax`: https://github.com/rakshasa/rtorrent/wiki/RPC-Migration-0.9
.. _`update the start script`: https://github.com/pyroscope/rtorrent-ps/blob/master/docs/DebianInstallFromSource.md#rtorrent-startup-script
.. _`GitHub releases`: https://github.com/pyroscope/pyrocore/releases
.. _`changelog`: https://github.com/pyroscope/pyrocore/blob/master/debian/changelog
.. _`list of commits`: https://github.com/pyroscope/pyrocore/commits/master
