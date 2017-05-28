Installation Guide
==================

This chapter presents you with different installation options.
If you start with an unconfigured host, consider using the automated
setup provided by the `pimp-my-box`_ project, which will install all
you need for a fully working torrenting setup including a default
configuration.

.. contents:: These are the steps for a manual installation:
    :local:

As you can see, installing the software package itself can be done in two ways,
choose one of them.
Afterwards, the freshly installed software *must* be provided with a configuration,
as described in the :doc:`setup`.


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

Installing Dependency Packages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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


Installing Python2
^^^^^^^^^^^^^^^^^^

For *Debian* and derivatives, the ``apt-get`` command in the previous section
already took care of everything.

Other Linux distributions usually come equipped with a Python 2.7 interpreter,
but on very new releases, Python 3 may be the default and Python 2.7 just an option.
In case you need to install Python 2, refer to `Installing Python on Linux`_ and
consider using `pyenv`_.

The following shows how you can check what version you have as the default (the
sample output is from *Ubuntu 15.04*):

.. code-block:: shell

    $ /usr/bin/python --version
    Python 2.7.9

Try calling ``/usr/bin/python2`` in case the above shows a ``3.*`` version.

.. _`Installing Python on Linux`: http://docs.python-guide.org/en/latest/starting/install/linux/
.. _`pyenv`: https://github.com/yyuu/pyenv#simple-python-version-management-pyenv


Installing the `pyrocore` Package
---------------------------------

Installing the software package itself can be done in two ways,
choose one of them.

.. warning::

    If you want to switch over from an old installation to one in ``~/.local``,
    then *move that old directory away*, before installation! Like this:

    .. code-block:: shell

        ( cd ~/lib && mv pyroscope pyroscope-$(date +'%Y-%m-%d').bak )

    Your existing configuration and data is not affected by this, but
    make sure you read the **migration instructions** in :doc:`updating`.


Option 1: Installing from GitHub
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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



Option 2: Installing from PyPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you chose to install a release version from the Python package repository (PyPI),
the *most simple but not best way* is calling ``pip install --user -U pyrocore``,
and make sure ``$HOME/.local/bin`` is in your ``$PATH``.
This way is OK if you just want to use the tools for metafile handling,
i.e. ``mktor``,  ``chtor``,  and ``lstor``, but not the *rTorrent* tools.


The **recommended way using a dedicated virtualenv** goes like this:

.. code-block:: shell

    mkdir -p ~/bin ~/.local
    /usr/bin/virtualenv --no-site-packages $_/pyroscope
    cd $_
    ln -nfs python bin/python-pyrocore
    ln -nfs $PWD/bin/python-pyrocore ~/bin
    . bin/activate
    xargs -n1 pip install -U <<<"pip setuptools wheel"
    pip uninstall -y distribute 2>/dev/null
    pip install -U "pyrocore[templating]"
    ln -nfs $(egrep -l '(from.pyrocore.scripts|entry_point.*pyrocore.*console_scripts)' $PWD/bin/*) ~/bin

    # Check success
    pyroadmin --version  # call "exec $SHELL -l" if this fails, and retry

If you previously had no ``~/bin`` directory, call ``exec $SHELL -l``
to register it in the ``PATH`` of your current terminal session
– especially if you see an error message like ``pyroadmin: command not found``.

If everything went OK, continue with the :doc:`setup`.
