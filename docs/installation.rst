Installation Guide
==================

This chapter presents you with different installation options.
If you start with an unconfigured host, consider using the automated
setup provided by the `pimp-my-box`_ project, which will install all
you need for a fully working torrenting setup including a default
configuration.

.. note::

    Unless otherwise indicated by using ``sudo`` or mentioning it in the text,
    installation commands should **not** be run as ``root``, but in your normal
    user account, or else one you specifically created for installing *rTorrent*
    and ``pyrocore``.

    When commands *and* their output are both contained in a code box, ``$``
    represents the command prompt of your shell, followed by the command you are
    supposed to enter. Do **not** enter the leading ``$``!

.. include:: include-xmlrpc-dialects.rst

.. _`pimp-my-box`: https://github.com/pyroscope/pimp-my-box#pimp-my-box


Preparing Your Host
-------------------

Before installing *pyrocore*, some software packages need to be available
on your machine, Python 2 among them.

On Debian-type systems (Debian, Ubuntu, Raspbian, …), the following ensures you have
everything you need, including packages necessary for installing from source:

.. code-block:: shell

    sudo apt-get install python python-dev python-virtualenv python-pip \
        python-setuptools python-pkg-resources git build-essential

On other Linux distributions, see the following section for further hints.

If you want to install everything in a dedicated user account,
e.g. for security reasons, this will create a ``rtorrent`` user
when entered into a ``root`` shell:

.. code-block:: shell

    groupadd rtorrent
    useradd -g rtorrent -G rtorrent,users -c "Torrent User" -s /bin/bash --create-home rtorrent
    chmod 750 ~rtorrent
    su - rtorrent -c "mkdir -p ~/bin"

Using such a dedicated account also makes sure you don't need to have fear
this software does anything malicious — if it did, it'd be contained in that
account. It also makes deinstallation or start-from-zero way less of a hassle.


Installing Python
^^^^^^^^^^^^^^^^^

Your Linux usually comes equipped with a Python 2.7 interpreter, but on very new
releases, Python 3 may be the default and Python 2.7 just an option.
In case you need to install Python 2, refer to `Installing Python on Linux`_ and
consider using `pyenv`_.

The following shows how you can check what version you have as the default (the
sample output is from *Ubuntu 15.04*):

.. code-block:: shell

    $ /usr/bin/python --version
    Python 2.7.9

.. _`Installing Python on Linux`: http://docs.python-guide.org/en/latest/starting/install/linux/
.. _`pyenv`: https://github.com/yyuu/pyenv#simple-python-version-management-pyenv


Installing From Source
----------------------

The recommended way to install this software is directly from its GitHub repository.
To do that, use the following commands:

.. code-block:: shell

    mkdir -p ~/bin ~/.local
    git clone "https://github.com/pyroscope/pyrocore.git" ~/.local/pyroscope

    # Pass "/usr/bin/python2", or whatever else fits, to the script as its
    # 1st argument, if the default of "/usr/bin/python" is not a suitable
    # version.
    ~/.local/pyroscope/update-to-head.sh

    # Check success
    pyroadmin --version  # call "exec $SHELL -l" if this fails, and retry

You can choose a different install directory, just change the paths
accordingly. If then anything fails, stop changing things and stick
to the trodden path.

If you previously had no ``~/bin`` directory, call ``exec $SHELL -l``
to register it in the ``PATH`` of your current terminal session
– especially if you see an error message like ``pyroadmin: command not found``.

If everything went OK, continue with the :doc:`setup`.

.. warning::

    If you want to switch over from an old installation based on
    subversion source (from `Google code <https://code.google.com/p/pyroscope/>`_),
    then *move that old directory away*, before installation! Like this:

    .. code-block:: shell

        ( cd ~/lib && mv pyroscope pyroscope-$(date +'%Y-%m-%d').bak )

    Your configuration and data is not affected by this.
