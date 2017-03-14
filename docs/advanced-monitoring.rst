.. Included in advanced.rst

Overview
^^^^^^^^

.. note::

    This feature is not finished and should not be considered stable at this time
    (i.e. it might change drastically).

The monitoring subsystem is an optional part of ``pyrotorque`` and
includes a web service that creates the monitoring pages which can be
viewed in your browser. There is a live view that continuously updates
current performance indicators of rTorrent and the host it runs on,
something similar to this:

.. figure:: http://i.imgur.com/ZAtTeci.png
   :align: center
   :alt: http://i.imgur.com/ZAtTeci.png

   Screenshot of the Monitoring View

**What can you see here?**

-  rTorrent and host uptimes.
-  rTorrent upload and download activity.
-  number of rTorrent items in total (♯), active (⚡), having a message
   (↯), complete (✔), incomplete (◑), seeding (▲), downloading (▼).
   started (☀), stopped (■).
-  and key host performance indicators.

The web interface follows *responsive web design*
(`RWD <https://en.wikipedia.org/wiki/Responsive_web_design>`_)
principles, which means it'll adapt to different devices and their
display size.

*(This is not yet implemented…)* Also, the ``StatsArchiver`` job of the
``pyrotorque`` demon writes a lot of statistical data to RRD archives
(*round robin database*) in 1 minute intervals. See
http://oss.oetiker.ch/rrdtool/doc/rrdtool.en.html for the theory behind
RRD, and the standard implementation used in a lot of systems.


Installation & Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As previously mentioned, monitoring is an optional part of
``pyrotorque``, so *first* see :ref:`QueueManager` on how to set it up in case
you didn't do that already. *After* ``pyrotorque`` is successfully
running, follow these additional steps to activate the web server.

A few additional Python libraries and external CSS/Javascript resources
need to be installed, which are not part of the core distribution.

#. Install current code and dependencies:

   .. code-block:: shell

      ~/.local/pyroscope/update-to-head.sh
      ~/.local/pyroscope/bin/pip install -r ~/.local/pyroscope/requirements-torque.txt

#. Activate the web server option by adding this to your ``~/.pyroscope/torque.ini``:

   .. code-block:: ini

      httpd.active = True

#. Download resources to ``~/.pyroscope/htdocs``:

   .. code-block:: shell

      pyroadmin --create-config

#. Finally, restart the demon:

   .. code-block:: shell

      pyrotorque --cron --restart
      # use "pyrotorque --fg --restart -v" instead, in case something doesn't work,
      # so you can directly read the log

If you didn't change the defaults, the web interface is now available
using the URL http://localhost:8042/, which will show you something
similar to the screen shot further above,


Additional Configuration Options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As with other config files, ``~/.pyroscope/torque.ini.default`` lists
all the available options and a short description. The following just
lists those that are quite often changed from the defaults.

``httpd.waitress.host``
    The address the web server listens on. The default is ``127.0.0.1`` (i.e.
    ``localhost``), and can be changed to ``0.0.0.0`` to listen to *any*
    interface. Note that the latter is only safe in your home LAN, behind a
    firewall or NAT. Add a *reverse proxy* to your Apache/nginx/… for
    exposing the web service to the internet, ideally adding password
    protection and using SSL.

``httpd.waitress.port``
    TCP port the web server listens on, default is ``8042``.

``httpd.json.disk_usage_path``
    Path used to get disk used/total, this
    can also be a list of paths to different partitions, separated by
    ``:``. The default is your home directory ``~``.


Sensors
^^^^^^^

The following values are gathered. Most (*all?*) of them are also
available per tracker (*and per media type?*).

Item Numbers
    ``d.total``, ``d.started``, ``d.stopped``, ``d.complete``,
    ``d.incomplete``, ``d.seeding``, ``d.leeching``, ``d.active``,
    ``d.messages``

    These are the associated view sizes; could be sampled
    more often, and the average values taken.

Item Size
    ``d.size_bytes``, ``d.left_bytes``, ``d.size_files``

Traffic
    ``d.up_rate``, ``d.down_rate``, ``d.skip_rate``

Resources
    ``open_sockets``, ``cputime``, ``pcpu``, ``pmem``, ``sz``, ``rsz``, ``vsz``

    See ``man ps`` for most of these.

Also, the usual machine statistics (CPU load, disk usage and I/O,
network traffic) are sampled (by ``collectd``, or using ``collectd``
plugins, or some system stats package?).


Later Extensions
^^^^^^^^^^^^^^^^

These are probably not sampled that often, or we need to define an extra
view to allow efficient sampling.

Ratios
    *As histogram counters?*

Events
    ``event_closed``, …

    Counters for all ``event.download.*`` events.

Peers
    ``peers_total``, ``peers_encrypted``, ``peers_incoming``, ``peers_obfuscated``,
    ``peers_preferred``, ``peers_snubbed``, ``peers_unwanted``

Files
    …

With some patches compiled into rTorrent, the additional values
``network.http.open``, and ``network.open_files`` are available.
