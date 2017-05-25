Custom Python Code
==================

You can write your own code for ``pyrocore`` implementing custom features,
by adding fields, your own command line scripts, or ``pyrotorque`` jobs.
You probably need a solid grasp of Python for this.


.. _CustomFields:

Defining Custom Fields
----------------------

.. include:: custom-fields.rst


.. _custom-template-helpers:

Adding Custom Template Helpers
------------------------------

In templating contexts, there is an empty ``c`` namespace (think ``custom`` or ``config``),
just like ``h`` for helpers.
You can populate that namespace with your own helpers as you need them,
from simple string transformations to calling external programs or web interfaces.

The following example illustrates the concept, and belongs into ``~/.pyroscope/config.py``.

.. code-block:: python

    def _hostname(ip):
        """Helper to e.g. look up peer IPs."""
        import socket

        return socket.gethostbyaddr(ip)[0] if ip else ip

    custom_template_helpers.hostname = _hostname

This demonstrates the call of that helper using a custom field,
a real use-case would be to resolve peer IPs and the like.

.. code-block:: shell

    $ rtcontrol -qo '{{d.fetch("custom_ip")}} → {{d.fetch("custom_ip") | c.hostname}}' // -/1
    8.8.8.8 → google-public-dns-a.google.com


.. _scripts:


Writing Your Own Scripts
------------------------

.. include:: custom-scripts.rst


.. _torque-custom-jobs:

Writing Custom Jobs
-------------------

.. include:: custom-jobs.rst
