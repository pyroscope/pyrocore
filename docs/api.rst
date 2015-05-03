.. _api:

API Documentation
=================

This is the full ``pyrocore`` API documentation, generated from source.

Packages & Modules
------------------

.. toctree::
   :maxdepth: 4

   apidoc/pyrocore


UML Diagrams
------------


All Classes
^^^^^^^^^^^

.. uml:: pyrocore -k

Exceptions
^^^^^^^^^^

.. uml:: -a2 -b
    ../src/pyrocore/error.py

rTorrent API
^^^^^^^^^^^^

.. uml:: -s1
    ../src/pyrocore/torrent/rtorrent.py

.. uml:: -s2
    ../src/pyrocore/torrent/engine.py


Filter Rules
^^^^^^^^^^^^

.. uml:: -s1
    ../src/pyrocore/util/matching.py

Scripts
^^^^^^^

.. uml:: pyrocore.scripts

Configuration
^^^^^^^^^^^^^

.. uml:: ../src/pyrocore/util/load_config.py

Metafile
^^^^^^^^

.. uml:: ../src/pyrocore/util/metafile.py

Tree Watch
^^^^^^^^^^

.. uml:: pyrocore.torrent.watch
