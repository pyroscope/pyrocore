.. Included in custom.rst

First off, you really need to know a good amount of Python to be able to do this.
But if you do, you can easily add your own background processing,
more versatile and more efficient than calling ``rtcontrol`` in a cron job.
The description here is terse, and mostly just tells you where to look for code examples,
and the basics of how a job implementation interacts with the core system.

.. note::

    While some effort will be spent on keeping the API backwards compatible,
    there is no guarantee of a stable API.
    Follow the commit log and changelogs of releases
    to get notified when you need to adapt your code.

Jobs are created during ``pyrotorque`` startup and registered with the scheduler.
Configuration is taken from the ``[TORQUE]`` section of ``torque.ini``,
and any ``job.«job-name».«param-name»`` setting contributes to a job named ``job-name``.
The ``handler``, ``schedule``, and ``active`` settings are used by the core,
the rest is passed to the ``handler`` class for customization and depends on the job type.

To locate the job implementation, ``handler`` contains a ``module.path:ClassName`` coordinate of its class.
So ``job.foo.handler = my.code::FooJob`` registers ``FooJob`` under the name ``foo``.
This means a job can be scheduled several times,
given the right configuration and if the job implementation is designed for it.
The given module must be importable of course,
i.e. ``pip install`` it into your ``pyrocore`` virtualenv.

The ``schedule`` defines the call frequency of the job's ``run`` method,
and ``active`` allows to easily disable a job without removing its configuration
– which is used to provide all the default jobs and their settings.
A job with ``active = False`` is simply ignored and not added to the scheduler on startup.

The most simple of jobs is the :any:`EngineStats` one.
Click on the link and then on ``[source]`` to see its source code.
Some noteworthy facts:

* the initializer gets passed a ``config`` parameter, holding all the settings from ``torque.ini``
  for a particular job instance, with the ``job.«name»`` prefix removed.
* ``pyrocore.config`` is imported as ``config_ini``, to not clash with the ``config`` dict passed into jobs.
* create a ``LOG`` attribute as shown, for your logging needs.
* to interact with *rTorrent*, open a proxy connection in ``run``.
* the :any:`InfluxDB` job shows how to access config parameters, e.g. ``self.config.dbname``.
* raise :any:`UserError` in the initializer to report configuration mishaps and prevent ``pyrotorque`` from starting.

More complex jobs that you can look at are the
:class:`pyrocore.torrent.watch.TreeWatch` and
:class:`pyrocore.torrent.queue.QueueManager` ones.
