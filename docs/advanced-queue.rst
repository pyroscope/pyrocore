.. Included in advanced.rst

Introduction
^^^^^^^^^^^^

The ``pyrotorque`` command is a daemon that handles background jobs.
At first, it was just a flexible torrent queue manager for starting items
one at a time (thus the name ``pyro-tor-que``), but it can now manage any job
that does some background processing for rTorrent, including custom
ones that you can add yourself.

It runs in the background parallel to rTorrent and has its own
scheduler to run automation jobs similar to rTorrent's ``schedule``
command — one of the jobs does start stopped items in a controlled fashion,
that is the queue manager part.

Besides the queue manager, the most important job type is ``TreeWatch``.
It reacts to file system events (via ``inotify``) to load new metafiles on the spot,
if you add the necessary configuration and activate it.
This way you have no delays at all, and no polling of watch directories in short intervals,
most often with no tangible result and just wasted CPU cycles.
Also, you can place the metafiles in arbitrary folders and sub-folders,
with just one configuration entry for the root folder to watch.
The queue is able to start items loaded via ``inotify``, i.e. both jobs can work together.

If you want to know about the gory details of the machinery behind this,
read :ref:`torque-custom-jobs`.


Initial Setup
^^^^^^^^^^^^^

Before you start configuring the daemon, you have to install some additional
Python dependencies it needs to do its work, also depending on what jobs
you activate in your configuration.
The following is how to install the *full* set of dependencies:

.. code-block:: shell

    ~/.local/pyroscope/bin/pip install -r ~/.local/pyroscope/requirements-torque.txt

Watch out for any errors, since this installs several Python extensions that *might*
need some ``*-dev`` OS packages available that you don't have on your machine.

The ``pyrotorque`` queue manager daemon relies on certain additions to ``rtorrent.rc``,
these are included in the standard ``pyrocore`` includes
that you added when you followed the :doc:`setup`.
If for whatever reason you need to add these manually,
the file ``~/.pyroscope/rtorrent.d/torque.rc.default`` holds these settings.

The daemon itself is configured by an additional configuration file
``~/.pyroscope/torque.ini`` containing the ``[TORQUE]`` section.
Most settings are already covered in ``torque.ini.default``,
including some short explanation what each setting does.
The next section shows how to customize these defaults.


.. _torque-config:

Configuration
^^^^^^^^^^^^^

Minimal Example
"""""""""""""""

The following is a **minimal** ``~/.pyroscope/torque.ini`` **configuration example**,
only changing a few values from the defaults to demonstrate key features:

.. code-block:: ini

    # "pyrotorque" configuration file
    #
    # For details, see https://pyrocore.readthedocs.io/en/latest/advanced.html#torque-config
    #

    [TORQUE]
    # Queue manager
    job.queue.active            = True
    job.queue.schedule          = second=*/5
    job.queue.intermission      = 60
    job.queue.downloading_max   = 3
    job.queue.startable         = is_ignored=0 message= prio>0
            [ prio>2 OR [ NOT [ traits=audio kind_25=jpg,png,tif,bmp ] ] ]
    job.queue.downloading       = [ prio>1 [ down>3 OR started<2i ] ]

    # Tree watch (works together with the queue)
    job.treewatch.active        = True
    job.treewatch.load_mode     = start
    job.treewatch.queued        = True
    job.treewatch.path          = /var/torrent/watch
    job.treewatch.cmd.nfo       = f.multicall=*.nfo,f.priority.set=2
    job.treewatch.cmd.jpg       = f.multicall=*.jpg,f.priority.set=2
    job.treewatch.cmd.png       = f.multicall=*.png,f.priority.set=2
    job.treewatch.cmd.tif       = f.multicall=*.tif,f.priority.set=0
    job.treewatch.cmd.target    = {{# set target path
        }}d.custom.set=targetdir,/var/torrent/done/{{label}}/{{relpath}}

Having a minimal configuration with just your changes is recommended, so
you get new defaults in later releases automatically.

See the
`default configuration <https://github.com/pyroscope/pyrocore/blob/master/src/pyrocore/data/config/torque.ini>`_
for **more parameters and what they mean**.

.. warning::

    If the folder tree specified in the ``path`` setting overlaps
    with the paths used in existing ‘watch’ schedules of ``rtorrent.rc``,
    then please either keep those paths apart, or disable those schedules
    (comment them out), *before* activating tree watch.

    Anything else will lead to confusing and inconsistent results.


Queue Settings Explained
""""""""""""""""""""""""

In the above example for the ``queue`` job,
``downloading_max`` counts started-but-incomplete items including those
that ignore commands. Only if there are fewer of these items in the client
than that number, a new item will be started.
This is the queue's length and thus the most important parameter.

The queue *never* stops any items, i.e. ``downloading_max`` is not enforced
and you can manually start more items than that if you want to.
That is also the reason items that should be under queue control
must be loaded in ‘normal’ mode, i.e. stopped.

Other queue parameters are the minimum number of
items in 'downloading' state named ``downloading_min``, which trumps
``start_at_once``, the maximum number of items to start in one run of the job.
Both default to ``1``. Since the default schedule is ``second=*/15``,
that means at most one item would be started every 15 seconds.

But that default is changed using the following two lines:

.. code-block:: ini

    job.queue.schedule          = second=*/5
    job.queue.intermission      = 60

This makes the queue manager check more often whether there is something startable,
but prevents it from starting the next batch of items
when the last start was less than ``intermission`` seconds ago.

The ``startable`` condition (repeated below for reference) prevents ignored items,
ones having a non-empty message,
and those with the lowest priority from being started.
Note that tree watch sets the priority of items loaded in ‘normal’ mode to zero
– that ``prio>0`` condition then excludes them from being started automatically some time later,
until you press ``+`` to increase that priority.
You can also delay not-yet-started items using the ``-`` key
until the item has a priority of zero (a/k/a ``off``).

.. code-block:: ini

    job.queue.startable = is_ignored=0 message= prio>0
            [ prio>2 OR [ NOT [ traits=audio kind_25=jpg,png,tif,bmp ] ] ]

This sample condition also adds the extra hurdle that audio downloads that don't stay below
a 25% threshold regarding contained images are **not** started automatically.
*Unless* you raise the priority to 3 (``high``) using the ``+`` key,
then they're fair game for the queue.
Go do all that with a plain rTorrent watch dir, in one line of configuration.

The parameter ``sort_fields`` is used to determinate in what order startable items are handled.
By default, higher priority items are started first, and age is used within each priority class.

Above, it was mentioned ``downloading_max`` counts started-but-incomplete items.
The exact definition of that classification can be changed using the
``downloading`` condition.
A given condition is *always* extended with ``is_active=1 is_complete=0``,
i.e. the started-but-incomplete requirement.

.. code-block:: ini

    job.queue.downloading = [ prio>1 [ down>3 OR started<2i ] ]

In plain English, this example says we only count items
that have a normal or high priority,
and transfer data or were started in the last 2 minutes.
The priority check means you can ‘hide’ started items from the queue by setting them to ``low``,
e.g. because they're awfully slow and prevent your full bandwidth from being used.

The second part automatically ignores stalled items unless just started.
This prevents disk trashing when a big item
is still creating its files and thus has no data transfer
– it looks stalled, but we do not want yet another item to be started and
increasing disk I/O even more, so the manager sees those idle but young items
as occupying a slot in the queue.


Tree Watch Details
""""""""""""""""""

The ``treewatch`` job is set to co-operate with the queue as previously explained,
and load items as ready to be started (i.e. in stopped state, but with normal priority).
Any ``load_mode`` that is not either ``start`` or ``started`` is considered
as equivalent to ``load.normal``.

.. code-block:: ini

    job.treewatch.active        = True
    job.treewatch.load_mode     = start
    job.treewatch.queued        = True

The configuration settings for ``load_mode`` and ``queued`` can also be changed
on a case-by-case basis. For that, one of the ‘flags’ ``load``, ``start``, or ``queued``
has to appear in the path of the loaded metafile
– either as a folder name, or else delimited by dots in the file name.
These examples should help with understanding how to use that::

    ☛ load and start these, ignoring what 'load_mode' says
    …/tv/start/foo.torrent
    …/movies/foo.start.torrent

    ☛ just load these, ignoring what 'load_mode' says
    …/tv/load/foo.torrent
    …/movies/foo.load.torrent

    ☛ always queue these, using the configured 'load_mode'
    …/tv/queue/foo.torrent
    …/movies/foo.queue.torrent

Should you have both ``start`` and ``load`` in a path, then ``start`` wins.

``path`` determines the root of the folder tree to watch for new metafiles
via registration with the ``inotify`` mechanism of Linux.
That means they are loaded milliseconds after they're written to disk,
without any excessive polling.

.. code-block:: ini

    job.treewatch.path          = /var/torrent/watch

You can provide more that one tree to watch, by separating the root folders with ``:``.

The ``cmd.«name»`` settings can be used to
provide additional load commands, executed during loading the new item,
*before* it is started (in case it is started at all).
This is equivalent to the commands you can append to a rTorrent ``load.*`` command.
They're added in the alphabetic order of their names.

.. code-block:: ini

    job.treewatch.cmd.nfo       = f.multicall=*.nfo,f.priority.set=2
    job.treewatch.cmd.jpg       = f.multicall=*.jpg,f.priority.set=2
    job.treewatch.cmd.png       = f.multicall=*.png,f.priority.set=2
    job.treewatch.cmd.tif       = f.multicall=*.tif,f.priority.set=0
    job.treewatch.cmd.target    = {{# set target path
        }}d.custom.set=targetdir,/var/torrent/done/{{label}}/{{relpath}}

The above example shows how to set any NFO files and JPG/PNG images to high priority,
and prevent downloading any TIF images by default.

Commands can be templates, see :ref:`tree-watch` for further details
on the ``target`` command.

.. note::

    In case no files are loaded after you activated tree watch, you can
    set ``trace_inotify`` to ``True`` to get detailed logs of all file
    system events as they are received.

    Also keep in mind that for now,
    if you add metafiles while the ``pyrotorque`` daemon is not running,
    you have to ``touch`` them manually after you have restarted it to load them.



Testing Your Configuration
""""""""""""""""""""""""""

After having completed your configuration, you're ready to **test it, by
following these steps**:

#. Execute ``rm ~/.pyroscope/run/pyrotorque`` to **prevent the watchdog from starting the manager**
   in the background.
#. **Stop any running daemon** process using ``pyrotorque --stop``,
   just in case.
#. Run ``pyrotorque --fg -v`` in a terminal, this will **start
   the job scheduler in the foreground** with verbose logging directly to
   that terminal, exactly what you need to check out if your configuration
   does what you intended. It also helps you to understand what goes on
   "under the hood".
#. If you applied **changes to your configuration**,
   stop the running scheduler by pressing CTRL-C, then **restart it**.
   Wash, rinse, repeat.
#. Press CTRL-C for the last time and call ``pyrotorque --status``,
   it should show that no daemon process is running.
#. Execute ``touch ~/.pyroscope/run/pyrotorque`` — this does
   **create the guard file again**, which must always exist if you want
   ``pyrotorque`` to run in the background (otherwise you'll just get an
   error message on the console or in the log, if you try to launch it).
#. **Wait up to 300 seconds**, and if your *rTorrent* configuration has the
   ``pyro_watchdog`` schedule as it should have, ``pyrotorque --status``
   will show that a daemon process was automatically started by that *rTorrent* schedule.
#. Enjoy, and **check** ``~/.pyroscope/log/torque.log`` for feedback from the daemon process.

If you want to restart the daemon running in the background immediately,
e.g. to **reload** ``torque.ini`` or after a software update, use
``pyrotorque --cron --restart``.


Built-in Jobs
^^^^^^^^^^^^^

The ``QueueManager`` is just one kind of job that can be run by
``pyrotorque``. It has an embedded scheduler that can run any number of
additional jobs, the following sections explain the built-in ones. Since
these jobs can be loaded from any available Python package, you can also
easily :ref:`write your own <torque-custom-jobs>`.

Jobs and their configuration are added in the ``[TORQUE]`` section, by
providing at least the parameters ``job.«NAME».handler`` and
``job.«NAME».schedule``. Depending on the handler, additional parameters
can/must be provided (see below for a list of built-in handlers and what they
do).

Details on the ``schedule`` parameter can be found
`here <https://apscheduler.readthedocs.io/en/v2.1.2/cronschedule.html>`_.
Multiple fields must be separated by spaces, so if a field value
contains a space, it must be quoted, e.g. ``hour=12 "day=3rd sun"``.
The ``handler`` parameter tells the system where to look for the job
implementation, see the handler descriptions below for the correct
values.


**QueueManager**

``pyrocore.torrent.queue:QueueManager`` manages queued downloads (i.e.
starts them in a controlled manner), it is described in detail
:ref:`further up on this page <torque-config>`.


**TreeWatch** (beta, not feature-complete)

``pyrocore.torrent.watch:TreeWatch`` watches a folder tree, which can be
nested arbitrarily. Loading of new ``.torrent`` files is immediate
(using ``libnotify``).

**TODO** Each sub-directory can contain a ``watch.ini`` configuration
file for parameters like whether to start new items immediately, and for
overriding the completion path.

See the explanation of the example configuration above and
:ref:`tree-watch` for further details.


**EngineStats**

``pyrocore.torrent.jobs:EngineStats`` runs once per minute, checks the
connection to rTorrent, and logs some statistical information.

You can change it to run only hourly by adding this to the
configuration: ``job.connstats.schedule      = hour=*``
