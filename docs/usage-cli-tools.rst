.. included from usage.rst

Overview of CLI Tools
^^^^^^^^^^^^^^^^^^^^^

``rtcontrol`` is the work-horse for rTorrent automation, it takes filter conditions
of the form ``‹field›=‹value›`` and selects a set of download items according to them.
That result can then be printed to the console according to a specified format,
or put into any rTorrent view for further inspection.
You can also take some bulk action on the selected items, e.g. starting, stopping, or deleting them.

``rtxmlrpc`` sends single XMLRPC commands to rTorrent, and ``rtmv`` allows you to move around the
data of download items in the file system, while continuing to seed that data.

The following commands help you with managing metafiles:

 * ``lstor`` safely lists their contents in various formats.
 * ``mktor`` creates them, with support for painless cross-seeding.
 * ``chtor`` changes existing metafiles, e.g. to add fast-resume information.
 * ``hashcheck`` simply checks data against a given metafile's piece hashes.

``pyrotorque`` is a companion daemon process to rTorrent that handles
automation tasks like queue management, instant metafile loading from
a directory tree via file system notifications, and other background tasks.

``pyroadmin`` is a helper for administrative tasks (mostly configuration handling).
and ``rtevent`` is experimental and incomplete.


Bash Completion
^^^^^^^^^^^^^^^

If you don't know what bash  completion is, or want to handle this later,
you can skip to :ref:`common-options`.


Using completion
""""""""""""""""

In case you don't know what ``bash`` completion looks like, watch this…

.. image:: videos/bash-completion.gif

Every time you're unsure what options you have, you can press ``TAB ↹`` twice
to get a menu of choices, and if you already know roughly what you want,
you can start typing and save keystrokes by pressing ``TAB ↹`` once, to
complete whatever you provided so far.

So for example, enter a partial command name like ``rtco`` and then ``TAB ↹`` to
get "``rtcontrol``", then type ``--`` followed by 2 times ``TAB ↹`` to get a list of
possible command line options.

Activating completion
"""""""""""""""""""""

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


.. _common-options:

Common Options
^^^^^^^^^^^^^^

All commands share some common options::

    --version          show program's version number and exit
    -h, --help         show this help message and exit
    -q, --quiet        omit informational logging
    -v, --verbose      increase informational logging
    --debug            always show stack-traces for errors
    --config-dir=DIR   configuration directory [~/.pyroscope]

Also see the :ref:`cli-usage` section for an automatically generated and thus
comprehensive listing of all the current options.


.. _mktor:

mktor
^^^^^

:ref:`cli-usage-mktor` creates ``*.torrent`` files (metafiles), given the **path to the data** in a
file, directory, or named pipe (more on that below) and a **tracker URL or alias name**
(see :ref:`config-ini` on how to define aliases).
Optionally, you can also set an additional comment and a different name for the
resulting torrent file. Peer exchange and DHT can be disabled by using
the ``--private`` option.

If you want to create metafiles in bulk, use one of the many options
a Linux shell offers you, among them:

 * *Anything* in the current directory:

   .. code-block:: shell

      ls -1 | xargs -d$'\n' -I{} mktor -p -o /tmp "{}" "$ANNOUNCE_URL"

 * Just for directories:

   .. code-block:: shell

      find . -mindepth 1 -maxdepth 1 -type d \! -name ".*" -print0 | sort -z \
          | xargs -0I{} mktor -p "{}" "$ANNOUNCE_URL"

If you create torrents for different trackers, they're
*automatically enabled for cross-seeding*, i.e. you can load several torrents for
exactly the same data into your client. For the technically inclined,
this is done by adding a unique key so that the info hash is always
different.
Use the ``--no-cross-seed`` option to disable this.
You can also set the ‘source’ field many trackers use for unique info hashes,
use ``-s info.source=LABEL`` for that.

To exclude files stored on disk from the resulting torrent, use the
``--exclude`` option to extend the list of standard glob patterns that
are ignored. These standard patterns are: ``core``, ``CVS``, ``.*``,
``*~``, ``*.swp``, ``*.tmp``, ``*.bak``, ``[Tt]humbs.db``,
``[Dd]esktop.ini``, and ``ehthumbs_vista.db``.

The ``--fast-resume`` option creates a second metafile
``*-resume.torrent`` that contains special entries which, when loaded
into rTorrent, makes it skip the redundant hashing phase (after all, you
hashed the files just now). It is **very** important to upload the
*other* file without ``resume`` in its name to your tracker, else you
cause leechers using rTorrent problems with starting their download.

As a unique feature, if you want to change the root directory of the
torrent to something different than the basename of the data directory,
you can do so with the ``--root-name`` option. This is especially useful
if you have hierarchical paths like ``documents/2009/myproject/specs`` -
normally, all the context information but ``specs`` would be lost on the
receiving side. Just don't forget to provide a symlink in your download
directory with the chosen name that points to the actual data directory.

Very few people will ever need that, but another advanced feature is
concurrent hashing — if the first argument is a named pipe (see the
``mkfifo`` man page), the filenames to be hashed are read from that
pipe. These names must be relative to the directory the named pipe
resides in, or put another way, the named pipe has to be created in the
same directory as the files to be hashed. For example, this makes it
possible to hash files as they arrive via FTP or are transcoded from one
audio format to another, reducing overall latency. See `the fifotest script`_
for a demonstration of the concept.

.. _`the fifotest script`: https://github.com/pyroscope/pyrocore/blob/master/src/tests/fifotest.sh


.. _lstor:

lstor
^^^^^

:ref:`cli-usage-lstor` lists the contents of bittorrent metafiles. The resulting
output looks like this::

    NAME pavement.torrent
    SIZE 3.6 KiB (0 * 32.0 KiB + 3.6 KiB)
    HASH 2D1A7E443D23907E5118FA4A1065CCA191D62C0B
    URL  http://example.com/
    PRV  NO (DHT/PEX enabled)
    TIME 2009-06-06 00:49:52
    BY   PyroScope 0.1.1

    FILE LISTING
    pavement.py                                                             3.6 KiB

    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    NAME tests.torrent
    SIZE 2.6 KiB (0 * 32.0 KiB + 2.6 KiB)
    HASH 8E37EB6F4D3807EB26F267D3A9D31C4262530AB2
    URL  http://example.com/
    PRV  YES (DHT/PEX disabled)
    TIME 2009-06-06 00:49:52
    BY   PyroScope 0.1.1

    FILE LISTING
    pyroscope tests/
        test_bencode.py                                                     2.6 KiB


``lstor`` has these options::

    --reveal       show full announce URL including keys
    --raw          print the metafile's raw content in all detail
    -V, --skip-validation
                   show broken metafiles with an invalid structure
    --output=KEY,KEY1.KEY2,...
                   select fields to print, output is separated by TABs;
                   note that __file__ is the path to the metafile,
                   __hash__ is the info hash, and __size__ is the data
                   size in byte

Starting with v0.3.6, you can select to output specific fields from the
metafile, like this::

    $ lstor -qo __hash__,info.piece\ length,info.name *.torrent
    00319ED92914E30C9104DA30BF39AF862513C4C8	262144	Execute My Liberty - The Cursed Way -- Jamendo - OGG Vorbis q7 - 2010.07.29 [www.jamendo.com]

This can also be used to rename ``‹infohash›.torrent`` metafiles
from a session directory to a human readable name,
using parts of the hash to ensure unique names::

    ls -1 *.torrent | egrep '^[0-9a-fA-F]{40}\.torrent' | while read i; do
        humanized="$(lstor -qo info.name,__hash__ "$i" | awk -F$'\t' '{print $1"-"substr($2,1,7)}')"
        mv "$i" "$humanized.torrent"
    done

And to see a metafile with all the guts hanging out, use the ``--raw``
option::

    {'announce': 'http://tracker.example.com/announce',
     'created by': 'PyroScope 0.3.2dev-r410',
     'creation date': 1268581272,
     'info': {'length': 10,
              'name': 'lab-rats',
              'piece length': 32768,
              'pieces': '<1 piece hashes>',
              'x_cross_seed': '142e0ae6d40bd9d3bcccdc8a9683e2fb'},
     'libtorrent_resume': {'bitfield': 0,
                           'files': [{'completed': 0,
                                      'mtime': 1283007315,
                                      'priority': 1}],
                           'peers': [],
                           'trackers': {'http://tracker.example.com/announce': {'enabled': 1}}},
     'rtorrent': {'chunks_done': 0,
                  'complete': 0,
                  'connection_leech': 'leech',
                  'connection_seed': 'seed',
                  'custom': {'activations': 'R1283007474P1283007494R1283007529P1283007537',
                             'kind': '100%_',
                             'tm_loaded': '1283007442',
                             'tm_started': '1283007474'},
                  'custom1': '',
                  'custom2': '',
                  'custom3': '',
                  'custom4': '',
                  'custom5': '',
                  'directory': '~/rtorrent/work',
                  'hashing': 0,
                  'ignore_commands': 1,
                  'key': 357633323,
                  'loaded_file': '~/rtorrent/.session/38DE398D332AE856B509EF375C875FACFA1C939F.torrent',
                  'priority': 2,
                  'state': 0,
                  'state_changed': 1283017194,
                  'state_counter': 4,
                  'throttle_name': '',
                  'tied_to_file': '~/rtorrent/watch/lab-rats.torrent',
                  'total_uploaded': 0,
                  'views': []}}


.. _chtor:

chtor
^^^^^

:ref:`cli-usage-chtor` is able to change common attributes of a metafile, or clean
any non-standard data from them (namely, rTorrent session information).

Note that ``chtor`` automatically changes only those metafiles whose
existing announce URL starts with the scheme and location of the new URL
when using ``--reannounce``. To change *all* given
metafiles unconditionally, use the ``--reannounce-all`` option and be
very sure you provide only those files you actually want to be changed.

``chtor`` only rewrites metafiles that were actually changed, and those
changes are first written to a temporary file, which is then renamed.


.. _rtcontrol:

rtcontrol
^^^^^^^^^

Purpose
"""""""

:ref:`cli-usage-rtcontrol` allows you to select torrents loaded into rTorrent using
various filter conditions. You can then either display the matches found
in any rTorrent view for further inspection,
list them to the console using flexible output formatting,
or perform some management action like starting and stopping torrents.
:ref:`RtXmlRpcExamples` shows examples for sending commands
that don't target a specific item.

For example, the command ``rtcontrol up=+0 up=-10k`` will list all
torrents that are currently uploading any data, but at a rate of below
10 KiB/s. See the :ref:`rtcontrol-examples` for more real-world examples,
and the following section on basics regarding the filter conditions.


.. _filter-conditions:

Filter Conditions
"""""""""""""""""

Filter conditions take the form ``‹field›=‹value›``, and by default
all given conditions must be met (AND). If a field name is omitted,
``name`` is assumed. Multiple values separated by a comma indicate
several possible choices (OR). ``!`` in front of a filter value
negates it (NOT). Use uppercase ``OR`` to combine multiple alternative
sets of conditions. And finally brackets can be used to group conditions
and alter the default "AND before OR" behaviour; be sure to separate
both the opening and closing bracket by white space from surrounding
text. ``NOT`` at the start of a bracket pair inverts the contained condition.


For string fields, the value is a
`glob pattern <http://docs.python.org/library/fnmatch.html>`_
which you are used to from shell filename patterns (``*``, ``?``, ``[a-z]``,
``[!a-z]``); glob patterns must match the whole field value, i.e. use
``*...*`` for 'contains' type searches. To use
`regex matches <http://docs.python.org/howto/regex.html>`_ instead of globbing,
enclose the pattern in slashes (``/regex/``). Since regex can express
anchoring the match at the head (``^``) or tail (``$``), they're by
default of the 'contains' type.
All string comparisons are case-ignoring.

For numeric fields, a leading ``+`` means greater than, a leading
``-`` means less than (just like with the standard ``find`` command).

Selection on fields that are lists of tags or names (e.g. ``tagged`` and
``views``) works by just providing the tags you want to search for. The
difference to the glob patterns for string fields is that tagged search
respects word boundaries (whitespace), and to get a match the given tag
just has to appear anywhere in the list (``bar`` matches on
``foo bar baz``).

In time filtering conditions (e.g. for the ``completed`` and ``loaded``
fields), you have three possible options to specify the value:

    #. time deltas in the form "``<number><unit>...``", where unit is a single
       upper- or lower-case letter and one of ``Y``\ ear, ``M``\ onth, ``W``\ eek,
       ``D``\ ay, ``H``\ our, m\ ``I``\ nute, or ``S``\ econd. The order is important
       (``y`` before ``m``), and a ``+`` before the delta means *older than*,
       while ``-`` means *younger than*.

       Example: ``-1m2w3d``
    #. a certain date and time in human readable form, where the date can be given in ISO
       (``Y-M-D``), American (``M/D/Y``), or European (``D.M.Y``) format.
       A date can be followed by a time, with minutes and seconds optional and
       separated by ``:``. Put either a space or a ``T`` between the date and
       the time.

       Example: ``+2010-08-15t14:50``
    #. absolute numerical UNIX timestamp, i.e. what ``ls -l --time-style '+%s'`` returns.

       Example: ``+1281876597``

See :ref:`useful-filter-conditions` for some concrete examples with an explanation of what they do.


Annealing Results
"""""""""""""""""

Using the ``--anneal`` option, you can add some pre-defined post-processing steps that
modify the current result set. You can use this option several times to combine processing
steps in the order given on the command line. Sorting is done first, and if anything changes,
the modified result is sorted again before applying the next step. Note that any ``--select``
restrictions are applied *after* annealing.

The available processing methods are these:

dupes+
    Adds any loaded item that shares the same base directory with any existing result item,
    or points to the same file. Note that symlinks are followed, but hardlinks are always
    considered independent (which they are when deleted).
    This is especially useful in combination with ``--cull`` to avoid leaving items
    with some or all of their files gone.

dupes-
    Removes items from the result that share the same path with any other loaded item,
    as described for ``dupes+``, that is not *also* part of the result.
    Again, combination with ``--cull`` is a typical use-case,
    to avoid deleting data of items that still need to be seeded,
    when only some of a set of duplicated items meet the deletion criteria.

dupes=
    Removes any items from the result that are *not* dupes, as defined above,
    leaving only the dupes. Combine with ``invert`` to only get singular items.

invert
    Invert the current selection, i.e. select any item in the *original* result
    (before any annealing happened) that is not in the *current* selection.

unique
    Ensures that only the *first* item in the result set having the same name
    as other items *in the result set* is kept. The others are removed.
    Note that unlike with ‘dupes’, the scope here is only the current result set,
    not *all* loaded items.


.. warning::

    If you use options that cause ``rtcontrol`` to request only a subset of
    all loaded items, then all ``dupes*`` methods will produce results that
    might be unexpected, since they look at *all* available items, not just
    the selected ones. And ‘all’ is different if you change the view, or
    use the ``-Q`` option – for that reason, you'll get a warning if you mix
    ``-A`` with these.


.. _rtxmlrpc:

rtxmlrpc
^^^^^^^^

:ref:`cli-usage-rtxmlrpc` allows you to call raw XMLRPC methods on the rTorrent
instance that you have specified in your configuration. See the
:ref:`usage information <cli-usage-rtxmlrpc>` for available options.

The method name and optional arguments are provided using standard shell
rules, i.e. where you would use ``^X throttle_down=slow,120`` in
rTorrent you just list the arguments in the usual shell way
(``rtxmlrpc throttle_down slow 120``). The rTorrent format is also
recognized though, but without any escaping rules (i.e. you cannot have
a ``,`` in your arguments then).

Remember that almost all commands require a ‘target’ as the first parameter
in newer rTorrent versions, and you have to provide that explicitly.
Thus, it must be ``rtxmlrpc view.size '' main``, with an extra empty argument
– otherwise you'll get a ``Unsupported target type found`` fault.

There are some special ways to write arguments of certain types:
``+‹number›`` and ``-‹number›`` send an integer value,
``@‹filename›`` or ``@-`` (for stdin) reads the file's content into a XMLRPC binary,
and finally ``[‹item1›〈,‹item2›,…〉`` produces an array of strings.
These typed arguments only cover some common use-cases,
at some point you have to write Python code to build up more intricate data structures.


To get a list of available methods, just call ``rtxmlrpc system.listMethods``.
The :ref:`RtXmlRpcExamples` section shows some typical examples for querying global information
and controlling rTorrent behaviour.


.. _rtmv:

rtmv
^^^^

With :ref:`cli-usage-rtmv`, you can move actively seeded data around at will.
Currently, it only knows one mode of operation, namely moving the data
directory or file and leave a symlink behind in its place (or fixing the
symlink if you move data around a second time). Watch this example that
shows what's going on internally::

    ~/bt/rtorrent/work$ rtmv lab-rats /tmp/ -v
    DEBUG    Found "lab-rats" for 'lab-rats'
    INFO     Moving to "/tmp/lab-rats"...
    DEBUG    Symlinking "~/bt/rtorrent/work/lab-rats"
    DEBUG    rename("~/bt/rtorrent/work/lab-rats", "/tmp/lab-rats")
    DEBUG    symlink("/tmp/lab-rats", "~/bt/rtorrent/work/lab-rats")
    INFO     Moved 1 path (skipped 0)

    $ rtmv /tmp/lab-rats /tmp/lab-mice -v
    DEBUG    Item path "~/bt/rtorrent/work/lab-rats" resolved to "/tmp/lab-rats"
    DEBUG    Found "lab-rats" for '/tmp/lab-rats'
    INFO     Moving to "/tmp/lab-mice"...
    DEBUG    Re-linking "~/bt/rtorrent/work/lab-rats"
    DEBUG    rename("/tmp/lab-rats", "/tmp/lab-mice")
    DEBUG    remove("~/bt/rtorrent/work/lab-rats")
    DEBUG    symlink("/tmp/lab-mice", "~/bt/rtorrent/work/lab-rats")


From the second example you can see that you can rename actively seeding
downloads in mid-flight, i.e. to fix a bad root directory name.

You can use ``rtmv`` in combination with ``rtcontrol --call`` for very flexible completion moving.
To facilitate this, if there is a double slash ``//`` in the
target path, it is always interpreted as a directory (i.e. you cannot
rename the source file in that case), and the partial path after the
``//`` is automatically created. This can be used in completion moving,
to create hierarchies for dynamic paths built from ``rtcontrol`` fields.
Since the part before the ``//`` has to exist beforehand, this won't go
haywire and create directory structures just anywhere.

.. note::

    Future modes of operation will include copying instead of moving, moving
    and fixing the download directory in rTorrent (like classical rtorrent
    completion event handling), and moving across devices (i.e. copying and
    then deleting).


.. _rtevent:

rtevent
^^^^^^^

**Not yet implemented**

:ref:`cli-usage-rtevent` handles rTorrent events and provides common implementations
for them, like completion moving. See EventHandling for details on using
it.
