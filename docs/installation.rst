Installing the Software
=======================

To install this software, use the following commands:

.. code-block:: shell

    # To be executed in a shell with your normal user account!
    mkdir -p ~/bin ~/lib
    git clone "https://github.com/pyroscope/pyrocore.git" ~/lib/pyroscope

    # Pass "/usr/bin/python2" or whatever to the script,
    # if "/usr/bin/python" is not a suitable version
    ~/lib/pyroscope/update-to-head.sh

    # Check success
    rtcontrol --version

You can choose a different install directory, just change the paths
accordingly.
