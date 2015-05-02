Installation Guide
==================

**TODO**
– see `the old docs <https://code.google.com/p/pyroscope/wiki/WikiSideBar>`_ for anything not yet moved.

*    Official release
*    Virtual environment
*    Linux setup from scratch
*    TroubleShooting
*    Updating Guide

.. note::

    Unless otherwise indicated by using ``sudo`` or mentioning it in the text,
    installation commands should *not* be run as ``root``, but in your normal
    user account, or else one you specifically created for installing *rTorrent*
    and ``pyrocore``.


Installing From Source
----------------------

To install this software from its GitHub repository, use the following commands:

.. code-block:: shell

    mkdir -p ~/bin ~/lib
    git clone "https://github.com/pyroscope/pyrocore.git" ~/lib/pyroscope

    # Pass "/usr/bin/python2", or whatever else fits, to the script,
    # if "/usr/bin/python" is not a suitable version (e.g. Python 3)
    ~/lib/pyroscope/update-to-head.sh

    # Check success
    pyroadmin --version

You can choose a different install directory, just change the paths
accordingly.

.. warning::

    If you want to switch over from an old installation based on
    subversion source (from `Google code <https://code.google.com/p/pyroscope/>`_),
    then *move that old directory away*, before installation! Like this:

    .. code-block:: shell

        ( cd ~/lib && mv pyroscope pyroscope-$(date +'%Y-%m-%d').bak )

    Your configuration and data is not affected by this.
