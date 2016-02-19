User's Manual
=============


Command Line Tools
------------------

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


mktor
^^^^^

::

    mktor [options] <dir-or-file> <tracker-url-or-alias>...

    Options:
      -p, --private         disallow DHT and PEX
      --no-date             leave out creation date
      -o PATH, --output-filename=PATH
                            optional file name for the metafile
      -r NAME, --root-name=NAME
                            optional root name (default is basename of the data
                            path)
      -x PATTERN [-x ...], --exclude=PATTERN [-x ...]
                            exclude files matching a glob pattern from hashing
      --comment=TEXT        optional human-readable comment
      -X LABEL, --cross-seed=LABEL
                            set explicit label for cross-seeding (changes info
                            hash)
      -H, --hashed, --fast-resume
                            create second metafile containing libtorrent fast-
                            resume information

``mktor`` creates ``*.torrent`` files (metafiles), given the path to a
file, directory, or named pipe (more on that below) and a tracker URL or
alias name (see UserConfiguration on how to define them). Optionally,
you can also set an additional comment and a different name for the
resulting torrent file. Peer exchange and DHT can be disabled by using
the ``--private`` option.

If you create torrents for different trackers, they're automatically
enabled for cross-seeding, i.e. you can load several torrents for
exactly the same data into your client. For the technically inclined,
this is done by adding a unique key so that the info hash is always
different.

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


lstor
^^^^^

``lstor`` lists the contents of bittorrent metafiles. The resulting
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


chtor
^^^^^

::

    Usage: chtor [options] <metafile>...

    Change attributes of a bittorrent metafile.

    Options:
      -n, --dry-run         don't write changes to disk, just tell what would
                            happen
      --no-skip             do not skip broken metafiles that fail the integrity
                            check
      -o PATH, --output-directory=PATH
                            optional output directory for the modified metafile(s)
      -p, --make-private    make torrent private (DHT/PEX disabled)
      -P, --make-public     make torrent public (DHT/PEX enabled)
      -s KEY=VAL [-s ...], --set=KEY=VAL [-s ...]
                            set a specific key to the given value
      -C, --clean           remove all non-standard data from metafile outside the
                            info dict
      -A, --clean-all       remove all non-standard data from metafile including
                            inside the info dict
      -X, --clean-xseed     like --clean-all, but keep libtorrent resume
                            information
      -R, --clean-rtorrent  remove all rTorrent session data from metafile
      -H DATAPATH, --hashed=DATAPATH, --fast-resume=DATAPATH
                            add libtorrent fast-resume information
      -a URL, --reannounce=URL
                            set a new announce URL, but only if the old announce
                            URL matches the new one
      --reannounce-all=URL  set a new announce URL on ALL given metafiles
      --no-cross-seed       when using --reannounce-all, do not add a non-standard
                            field to the info dict ensuring unique info hashes
      --comment=TEXT        set a new comment (an empty value deletes it)
      --bump-date           set the creation date to right now
      --no-date             remove the 'creation date' field

``chtor`` is able to change common attributes of a metafile, or clean
any non-standard data from them (namely, rTorrent session information).

Note that ``chtor`` automatically changes only those metafiles whose
existing announce URL starts with the scheme and location of the new URL
when using ``--reannounce``. To change *all* given
metafiles unconditionally, use the ``--reannounce-all`` option and be
very sure you provide only those files you actually want to be changed.

``chtor`` only rewrites metafiles that were actually changed, and those
changes are first written to a temporary file, which is then renamed.


rtcontrol
^^^^^^^^^

``rtcontrol`` allows you to select torrents loaded into rTorrent using
various filter conditions. You can then either display the matches found
in any rTorrent view, list them to the console using flexible output
formatting, or perform some management action like starting and stopping
torrents.

For example, the command ``rtcontrol up=+0 up=-10k`` will list all
torrents that are currently uploading any data, but at a rate of below
10 KiB/s. See the :ref:`rtcontrol-examples` for more real-world examples.


rtxmlrpc
^^^^^^^^

``rtxmlrpc`` allows you to call raw XMLRPC methods on the rTorrent
instance that you have specified in your configuration. See the `usage
information <CliUsage#rtxmlrpc.md>`_ for available options.

The method name and optional arguments are provided using standard shell
rules, i.e. where you would use ``^X throttle_down=slow,120`` in
rTorrent you just list the arguments in the usual shell way
(``rtxmlrpc throttle_down slow 120``). The rTorrent format is also
recognized though, but without any escaping rules (i.e. you cannot have
a '``,``' in your arguments then).

To get a list of available methods, just call ``rtxmlrpc system.listMethods``.
See RtXmlRpcExamples for a list of useful calls. **TODO** (fix reference)


rtmv
^^^^

::

    Usage: rtmv [options] <source>... <target>

    Move data actively seeded in rTorrent.

      -n, --dry-run         don't move data, just tell what would happen
      -F, --force-incomplete
                            force a move of incomplete data

With ``rtmv``, you can move actively seeded data around at will.
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


rtevent
^^^^^^^

**Not yet implemented**

``rtevent`` handles rTorrent events and provides common implementations
for them, like completion moving. See EventHandling for details on using
it.


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


.. _rtcontrol-examples:

“rtcontrol” Examples
--------------------

For now see https://github.com/pyroscope/pyroscope/blob/wiki/RtControlExamples.md


.. _output-templates:

Using Output Templates
----------------------

For now, see https://github.com/pyroscope/pyroscope/blob/wiki/OutputTemplates.md
