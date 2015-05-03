Installation Guide
==================

**TODO**
– see `the old docs <https://code.google.com/p/pyroscope/wiki/WikiSideBar>`_ for anything not yet moved.

*    Official release
*    Virtual environment
*    Linux setup from scratch

.. note::

    Unless otherwise indicated by using ``sudo`` or mentioning it in the text,
    installation commands should *not* be run as ``root``, but in your normal
    user account, or else one you specifically created for installing *rTorrent*
    and ``pyrocore``.


Preparing Your Host
-------------------

Before installing *pyrocore*, some software packages need to be available
on your machine, Python 2 among them.

On Debian-type systems (Debian, Ubuntu, Mint, …), the following ensures you have
everything you need, including packages necessary for installing from source:

.. code-block:: shell

    sudo apt-get install python python-dev python-virtualenv python-pip \
        python-setuptools python-pkg-resources git build-essential

On other Linux distributions, see the following section for further hints.


Installing Python
^^^^^^^^^^^^^^^^^

Your Linux usually comes equipped with a Python 2.7 interpreter, but on very new
releases, Python 3 may be the default and Python 2.7 just an option.
In case you need to install Python, refer to `Installing Python on Linux`_ and
consider using `pyenv`_.

.. _`Installing Python on Linux`: http://docs.python-guide.org/en/latest/starting/install/linux/
.. _`pyenv`: https://github.com/yyuu/pyenv#simple-python-version-management-pyenv


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
