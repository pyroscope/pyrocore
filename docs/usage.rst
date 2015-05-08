User's Manual
=============

**TODO**
– see `the old docs <https://code.google.com/p/pyroscope/wiki/WikiSideBar>`_ for anything not yet moved.

*    CLI Tools Overview
*    Using rtcontrol
*    Templating


Bash Completion
---------------

Using completion
^^^^^^^^^^^^^^^^

In case you don't know what ``bash`` completion looks like, watch this…

.. image:: videos/bash-completion.gif

Every time you're unsure what options you have, you can press *TAB* twice
to get a menu of choices, and if you already know roughly what you want,
you can start typing and save keystrokes by pressing *TAB* once, to
complete whatever you provided so far.

So for example, enter a partial command name like ``rtco`` and *TAB* to
get "``rtcontrol``", then type ``--`` and *TAB* twice to get a list of
possible command line options.

Activating completion
^^^^^^^^^^^^^^^^^^^^^

To add ``pyrocore``'s completion definitions to your shell, call these commands:

.. code-block:: shell

    pyroadmin --create-config
    touch ~/.bash_completion
    grep /\.pyroscope/ ~/.bash_completion >/dev/null || \
        echo >>.bash_completion ". ~/.pyroscope/bash-completion.default"
    . /etc/bash_completion

After that, completion should work, see the above section for things to try out.

.. note::

    On *Ubuntu*, you need to have the ``bash-completion`` package
    installed on your machine. Other Linux systems will have a similar
    pre-condition.
