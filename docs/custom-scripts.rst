.. Included in custom.rst

.. _intro:

Introduction
^^^^^^^^^^^^

The ``pyrocore`` Python package contains powerful helper classes that
make remote access to *rTorrent* child's play (see :ref:`api`).
And your tools get the same *Look & Feel* like the built-in *PyroScope*
commands, as long as you use the provided base class
:class:`pyrocore.scripts.base.ScriptBaseWithConfig`.

See for yourself:

.. code-block:: python

    #! /usr/bin/env python-pyrocore
    # -*- coding: utf-8 -*-

    # Enter the magic kingdom
    from pyrocore import config
    from pyrocore.scripts import base


    class UserScript(base.ScriptBaseWithConfig):
        """
            Just some script you wrote.
        """

        # argument description for the usage information
        ARGS_HELP = "<arg_1>... <arg_n>"

        # set your own version
        VERSION = '1.0'

        # (optionally) define your licensing
        COPYRIGHT = u'Copyright (c) …'

        def add_options(self):
            """ Add program options.
            """
            super(UserScript, self).add_options()

            # basic options
            ##self.add_bool_option("-n", "--dry-run",
            ##    help="don't do anything, just tell what would happen")


        def mainloop(self):
            """ The main loop.
            """
            # Grab your magic wand
            proxy = config.engine.open()

            # Wave it
            torrents = list(config.engine.items())

            # Abracadabra
            print "You have loaded %d torrents tracked by %d trackers." % (
                len(torrents),
                len(set(i.alias for i in torrents)),
            )

            self.LOG.info("XMLRPC stats: %s" % proxy)


    if __name__ == "__main__":
        base.ScriptBase.setup()
        UserScript().run()

Another full example is the `dynamic seed throttle script`_.

.. note::

    If you wondered about the first line referring to a ``python-pyrocore``
    command, that is an alias the installation scripts create for
    the Python interpreter of the *pyrocore* virtualenv. This way,
    your script will always use the correct environment that actually
    offers the right packages.

For simple calls, you can also use the ``rtxmlrpc`` command on a shell
prompt, see :ref:`RtXmlRpcExamples` for that. For a reference of the *rTorrent*
XMLRPC interface, see :ref:`RtXmlRpcReference`. Another common way to add your
own extensions is :ref:`CustomFields`, usable by ``rtcontrol`` just
like built-in ones.

.. _`dynamic seed throttle script`:
    https://github.com/pyroscope/pyrocore/blob/master/docs/examples/rt_cron_throttle_seed


Interactive use in a Python shell
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also access rTorrent interactively, like this:

.. code-block:: python

    >>> from pyrocore import connect
    >>> rt = connect()
    >>> len(set(i.tracker for i in rt.items()))
    2
    >>> rt.engine_software
    'rTorrent 0.9.2/0.13.2'
    >>> rt.uptime
    1325.6771779060364
    >>> proxy = rt.open()
    >>> len(proxy.system.listMethods())
    1033


Using ``pyrocore`` as a library in other projects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The example in the first section is an easy way to create user-defined
scripts. If you want to use ``pyrocore``'s features in another runtime
environment, you just have to load the configuration manually (what
:class:`pyrocore.scripts.base.ScriptBaseWithConfig`
does for you otherwise).

.. code-block:: python

    # Details depend on the system you want to extend, of course
    from some_system import plugin
    from pyrocore import error
    from pyrocore.util import load_config

    def my_rtorrent_plugin():
        """ Initialize plugin.
        """
        try:
            load_config.ConfigLoader().load()
        except error.LoggableError as exc:
            # Handle accordingly...
        else:
            # Do some other stuff...

    plugin.register(my_rtorrent_plugin)


Code snippets
^^^^^^^^^^^^^

.. note::

    The following snippets are meant to be placed and executed within
    the ``mainloop`` of the script skeleton found in :ref:`intro`.


Accessing the files in a download item
""""""""""""""""""""""""""""""""""""""

To get all the files for several items at once, we combine
``system.multicall`` and ``f.multicall`` to one big efficient mess.

.. code-block:: python

    from pprint import pprint, pformat

    # The attributes we want to fetch
    methods = [
        "f.get_path",
        "f.get_size_bytes",
        "f.get_last_touched",
        "f.get_priority",
        "f.is_created",
        "f.is_open",
    ]

    # Build the multicall argument
    f_calls = [method + '=' for method in methods]
    calls = [{"methodName": "f.multicall", "params": [infohash, 0] + f_calls}
        for infohash in self.args
    ]

    # Make the calls
    multicall = proxy.system.multicall
    result = multicall(calls)

    # Print the results
    for infohash, (files,) in zip(self.args, result):
        print ("~~~ %s [%d file(s)] " % (infohash, len(files))).ljust(78, '~')
        pprint(files)
    self.LOG.info("Multicall stats: %s" % multicall)
