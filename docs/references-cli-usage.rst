.. automatically generated using 'paver gendocs'.

.. contents::
    :local:

.. note::

    The help output presented here applies to version ``0.5.1`` of the tools.

.. _cli-usage-chtor:

chtor
^^^^^

::

    Usage: chtor [options] <metafile>...

    Change attributes of a bittorrent metafile.

    For more details, see the full documentation at

        https://pyrocore.readthedocs.io/

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -q, --quiet           omit informational logging
      -v, --verbose         increase informational logging
      --debug               always show stack-traces for errors
      --cron                run in cron mode (with different logging configuration)
      --config-dir=DIR      configuration directory [~/.pyroscope]
      --config-file=PATH    additional config file(s) to read
      -D KEY=VAL [-D ...], --define=KEY=VAL [-D ...]
                            override configuration attributes
      -n, --dry-run         don't write changes to disk, just tell what would happen
      -V, --no-skip         do not skip broken metafiles that fail the integrity check
      -o PATH, --output-directory=PATH
                            optional output directory for the modified metafile(s)
      -p, --make-private    make torrent private (DHT/PEX disabled)
      -P, --make-public     make torrent public (DHT/PEX enabled)
      -s KEY=VAL [-s ...], --set=KEY=VAL [-s ...]
                            set a specific key to the given value; omit the '=' to delete a key
      -r KEYcREGEXcSUBSTc [-r ...], --regex=KEYcREGEXcSUBSTc [-r ...]
                            replace pattern in a specific key by the given substitution
      -C, --clean           remove all non-standard data from metafile outside the info dict
      -A, --clean-all       remove all non-standard data from metafile including inside the info dict
      -X, --clean-xseed     like --clean-all, but keep libtorrent resume information
      -R, --clean-rtorrent  remove all rTorrent session data from metafile
      -H DATAPATH, --hashed=DATAPATH, --fast-resume=DATAPATH
                            add libtorrent fast-resume information (use {} in place of the torrent's name in DATAPATH)
      -a URL, --reannounce=URL
                            set a new announce URL, but only if the old announce URL matches the new one
      --reannounce-all=URL  set a new announce URL on ALL given metafiles
      --no-ssl              force announce URL to 'http'
      --no-cross-seed       when using --reannounce-all, do not add a non-standard field to the info dict ensuring unique info hashes
      --comment=TEXT        set a new comment (an empty value deletes it)
      --bump-date           set the creation date to right now
      --no-date             remove the 'creation date' field

.. _cli-usage-hashcheck:

hashcheck
^^^^^^^^^

::

    Usage: hashcheck [options] <metafile> [<data-dir-or-file>]

    Check a bittorrent metafile.

    For more details, see the full documentation at

        https://pyrocore.readthedocs.io/

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -q, --quiet           omit informational logging
      -v, --verbose         increase informational logging
      --debug               always show stack-traces for errors
      --cron                run in cron mode (with different logging configuration)
      --config-dir=DIR      configuration directory [~/.pyroscope]
      --config-file=PATH    additional config file(s) to read
      -D KEY=VAL [-D ...], --define=KEY=VAL [-D ...]
                            override configuration attributes

.. _cli-usage-lstor:

lstor
^^^^^

::

    Usage: lstor [options] <metafile>...

    List contents of a bittorrent metafile.

    For more details, see the full documentation at

        https://pyrocore.readthedocs.io/

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -q, --quiet           omit informational logging
      -v, --verbose         increase informational logging
      --debug               always show stack-traces for errors
      --cron                run in cron mode (with different logging configuration)
      --reveal              show full announce URL including keys
      --raw                 print the metafile's raw content in all detail
      -V, --skip-validation
                            show broken metafiles with an invalid structure
      -o KEY,KEY1.KEY2,..., --output=KEY,KEY1.KEY2,...
                            select fields to print, output is separated by TABs; note that __file__ is the path to the metafile,
                            __hash__ is the info hash, and __size__ is the data size in bytes

.. _cli-usage-mktor:

mktor
^^^^^

::

    Usage: mktor [options] <dir-or-file> <tracker-url-or-alias>... | <magnet-uri>

    Create a bittorrent metafile.

    If passed a magnet URI as the only argument, a metafile is created
    in the directory specified via the configuration value 'magnet_watch',
    loadable by rTorrent. Which means you can register 'mktor' as a magnet:
    URL handler in Firefox.

    For more details, see the full documentation at

        https://pyrocore.readthedocs.io/

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -q, --quiet           omit informational logging
      -v, --verbose         increase informational logging
      --debug               always show stack-traces for errors
      --cron                run in cron mode (with different logging configuration)
      --config-dir=DIR      configuration directory [~/.pyroscope]
      --config-file=PATH    additional config file(s) to read
      -D KEY=VAL [-D ...], --define=KEY=VAL [-D ...]
                            override configuration attributes
      -p, --private         disallow DHT and PEX
      --no-date             leave out creation date
      -o PATH, --output-filename=PATH
                            optional file name (or target directory) for the metafile
      -r NAME, --root-name=NAME
                            optional root name (default is basename of the data path)
      -x PATTERN [-x ...], --exclude=PATTERN [-x ...]
                            exclude files matching a glob pattern from hashing
      --comment=TEXT        optional human-readable comment
      -s KEY=VAL [-s ...], --set=KEY=VAL [-s ...]
                            set a specific key to the given value; omit the '=' to delete a key
      --no-cross-seed       do not automatically add a field to the info dict ensuring unique info hashes
      -X LABEL, --cross-seed=LABEL
                            set additional explicit label for cross-seeding (changes info hash)
      -H, --hashed, --fast-resume
                            create second metafile containing libtorrent fast-resume information

.. _cli-usage-pyroadmin:

pyroadmin
^^^^^^^^^

::

    Usage: pyroadmin [options]

    Support for administrative tasks.

    For more details, see the full documentation at

        https://pyrocore.readthedocs.io/

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -q, --quiet           omit informational logging
      -v, --verbose         increase informational logging
      --debug               always show stack-traces for errors
      --cron                run in cron mode (with different logging configuration)
      --config-dir=DIR      configuration directory [~/.pyroscope]
      --config-file=PATH    additional config file(s) to read
      -D KEY=VAL [-D ...], --define=KEY=VAL [-D ...]
                            override configuration attributes
      --create-config       create default configuration
      --remove-all-rc-files
                            write new versions of BOTH .rc and .rc.default files, and remove stale ones
      --dump-config         pretty-print configuration including all defaults
      --create-import=GLOB-PATTERN
                            create import file for a '.d' directory
      --dump-rc             pretty-print dynamic commands defined in 'rtorrent.rc'
      -o KEY,KEY1.KEY2=DEFAULT,..., --output=KEY,KEY1.KEY2=DEFAULT,...
                            select fields to print, output is separated by TABs; default values can be provided after the key
      --reveal              show config internals and full announce URL including keys
      --screenlet           create screenlet stub

.. _cli-usage-pyrotorque:

pyrotorque
^^^^^^^^^^

::

    Usage: pyrotorque [options]

    rTorrent queue manager & daemon.

    For more details, see the full documentation at

        https://pyrocore.readthedocs.io/

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -q, --quiet           omit informational logging
      -v, --verbose         increase informational logging
      --debug               always show stack-traces for errors
      --cron                run in cron mode (with different logging configuration)
      --config-dir=DIR      configuration directory [~/.pyroscope]
      --config-file=PATH    additional config file(s) to read
      -D KEY=VAL [-D ...], --define=KEY=VAL [-D ...]
                            override configuration attributes
      -n, --dry-run         advise jobs not to do any real work, just tell what would happen
      --no-fork, --fg       Don't fork into background (stay in foreground and log to console)
      --stop                Stop running daemon
      --restart             Stop running daemon, then fork into background
      -?, --status          Check daemon status
      --pid-file=PATH       file holding the process ID of the daemon, when running in background
      --guard-file=PATH     guard file for the process watchdog

.. _cli-usage-rtcontrol:

rtcontrol
^^^^^^^^^

::

    Usage: rtcontrol [options] <filter>...

    Control and inspect rTorrent from the command line.

    Filter expressions take the form "<field>=<value>", and all expressions must
    be met (AND). If a field name is omitted, "name" is assumed. You can also use
    uppercase OR to build a list of alternative conditions.

    For numeric fields, a leading "+" means greater than, a leading "-" means less
    than. For string fields, the value is a glob pattern (*, ?, [a-z], [!a-z]), or
    a regex match enclosed by slashes. All string comparisons are case-ignoring.
    Multiple values separated by a comma indicate several possible choices (OR).
    "!" in front of a filter value negates it (NOT).

    See https://pyrocore.readthedocs.io/en/latest/usage.html#rtcontrol for more.

    Examples:
      - All 1:1 seeds         ratio=+1
      - All active torrents   xfer=+0
      - All seeding torrents  up=+0
      - Slow torrents         down=+0 down=-5k
      - Older than 2 weeks    completed=+2w
      - Big stuff             size=+4g
      - 1:1 seeds not on NAS  ratio=+1 'realpath=!/mnt/*'
      - Music                 kind=flac,mp3

    Use --help to get a list of all options.
    Use --help-fields to list all fields and their description.

    For more details, see the full documentation at

        https://pyrocore.readthedocs.io/

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -q, --quiet           omit informational logging
      -v, --verbose         increase informational logging
      --debug               always show stack-traces for errors
      --cron                run in cron mode (with different logging configuration)
      --config-dir=DIR      configuration directory [~/.pyroscope]
      --config-file=PATH    additional config file(s) to read
      -D KEY=VAL [-D ...], --define=KEY=VAL [-D ...]
                            override configuration attributes
      --help-fields         show available fields and their description
      -n, --dry-run         don't commit changes, just tell what would happen
      --detach              run the process in the background
      -i, --interactive     interactive mode (prompt before changing things)
      --yes                 positively answer all prompts (e.g. --delete --yes)
      -S, --shell           escape output following shell rules
      -0, --nul, --print0   use a NUL character instead of a linebreak after items
      -c, --column-headers  print column headers
      -+, --stats           add sum / avg / median of numerical fields
      --summary             print only statistical summary, without the items
      --json                dump all items as JSON (use '-o f1,f2,...' to specify fields)
      -o FORMAT, --output-format=FORMAT
                            specify display format (use '-o-' to disable item display)
      -O FILE, --output-template=FILE
                            pass control of output formatting to the specified template
      -s [-]FIELD[,...] [-s...], --sort-fields=[-]FIELD[,...] [-s...]
                            fields used for sorting, descending if prefixed with a '-'; '-s*' uses output field list
      -r, --reverse-sort    reverse the sort order
      -A MODE [-A...], --anneal=MODE [-A...]
                            modify result set using some pre-defined methods
      -/ [N-]M, --select=[N-]M
                            select result subset by item position (counting from 1)
      -V, --view-only       show search result only in default ncurses view
      --to-view=NAME        show search result only in named ncurses view
      --tee-view            ADDITIONALLY show search results in ncurses view (modifies -V and --to-view behaviour)
      --from-view=NAME      select only items that are on view NAME (NAME can be an info hash to quickly select a single item)
      -M NAME, --modify-view=NAME
                            get items from given view and write result back to it (short-cut to combine --from-view and --to-view)
      -Q LEVEL, --fast-query=LEVEL
                            enable query optimization (=: use config; 0: off; 1: safe; 2: danger seeker) [=]
      --call=CMD            call an OS command pattern in the shell
      --spawn=CMD [--spawn ...]
                            execute OS command pattern(s) directly
      --start               start torrent
      --close, --stop       stop torrent
      -H, --hash-check      hash-check torrent (implies -i)
      --delete              remove torrent from client (implies -i)
      --purge, --delete-partial
                            delete PARTIAL data files and remove torrent from client (implies -i)
      --cull, --exterminate, --delete-all
                            delete ALL data files and remove torrent from client (implies -i)
      -T NAME, --throttle=NAME
                            assign to named throttle group (NULL=unlimited, NONE=global) (implies -i)
      --tag="TAG +TAG -TAG..."
                            add or remove tag(s)
      --custom=KEY=VALUE    set value of 'custom_KEY' field (KEY might also be 1..5)
      --exec=CMD, --xmlrpc=CMD
                            execute XMLRPC command pattern (implies -i)
      --ignore=0|1          set 'ignore commands' status on torrent
      --prio=0|1|2|3        set priority of torrent
      -F, --flush           flush changes immediately (save session data)

    Fields are:
      active                last time a peer was connected
      alias                 tracker alias or domain
      completed             time download was finished
      custom_KEY            named rTorrent custom attribute, e.g. 'custom_completion_target'
      directory             directory containing download data
      done                  completion in percent
      down                  download rate
      files                 list of files in this item
      fno                   number of files in this item
      hash                  info hash
      is_active             download active?
      is_complete           download complete?
      is_ghost              has no data file or directory?
      is_ignored            ignore commands?
      is_multi_file         single- or multi-file download?
      is_open               download open?
      is_private            private flag set (no DHT/PEX)?
      kind                  ALL kinds of files in this item (the same as kind_0)
      kind_N                file types that contribute at least N% to the item's total size
      leechtime             time taken from start to completion
      loaded                time metafile was loaded
      message               current tracker message
      metafile              path to torrent file
      name                  name (file or root directory)
      path                  path to download data
      prio                  priority (0=off, 1=low, 2=normal, 3=high)
      ratio                 normalized ratio (1:1 = 1.0)
      realpath              real path to download data
      seedtime              total seeding time after completion
      sessionfile           path to session file
      size                  data size
      started               time download was FIRST started
      stopped               time download was last stopped or paused
      tagged                has certain tags? (not related to the 'tagged' view)
      throttle              throttle group name (NULL=unlimited, NONE=global)
      tracker               first in the list of announce URLs
      traits                automatic classification of this item (audio, video, tv, movie, etc.)
      up                    upload rate
      uploaded              amount of uploaded data
      views                 views this item is attached to
      xfer                  transfer rate

    Format specifiers are:
      delta                 Format a UNIX timestamp to a delta (relative to now).
      duration              Format a duration value in seconds to a readable form.
      iso                   Format a UNIX timestamp to an ISO datetime string.
      json                  JSON serialization.
      mtime                 Modification time of a path.
      pathbase              Base name of a path.
      pathdir               Directory containing the given path.
      pathext               Extension of a path (including the '.').
      pathname              Base name of a path, without its extension.
      pc                    Scale a ratio value to percent.
      raw                   Switch off the default field formatter.
      strip                 Strip leading and trailing whitespace.
      subst                 Replace regex with string.
      sz                    Format a byte sized value.

    Append format specifiers using a '.' to field names in '-o' lists,
    e.g. 'size.sz' or 'completed.raw.delta'.

.. _cli-usage-rtevent:

rtevent
^^^^^^^

::

    Usage: rtevent [options] <event> <infohash> [<args>...]

    Handle rTorrent events.

    For more details, see the full documentation at

        https://pyrocore.readthedocs.io/

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -q, --quiet           omit informational logging
      -v, --verbose         increase informational logging
      --debug               always show stack-traces for errors
      --cron                run in cron mode (with different logging configuration)
      --config-dir=DIR      configuration directory [~/.pyroscope]
      --config-file=PATH    additional config file(s) to read
      -D KEY=VAL [-D ...], --define=KEY=VAL [-D ...]
                            override configuration attributes
      --no-fork, --fg       Don't fork into background (stay in foreground, default for terminal use)

.. _cli-usage-rtmv:

rtmv
^^^^

::

    Usage: rtmv [options] <source>... <target>

    Move data actively seeded in rTorrent.

    For more details, see the full documentation at

        https://pyrocore.readthedocs.io/

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -q, --quiet           omit informational logging
      -v, --verbose         increase informational logging
      --debug               always show stack-traces for errors
      --cron                run in cron mode (with different logging configuration)
      --config-dir=DIR      configuration directory [~/.pyroscope]
      --config-file=PATH    additional config file(s) to read
      -D KEY=VAL [-D ...], --define=KEY=VAL [-D ...]
                            override configuration attributes
      -n, --dry-run         don't move data, just tell what would happen
      -F, --force-incomplete
                            force a move of incomplete data

.. _cli-usage-rtxmlrpc:

rtxmlrpc
^^^^^^^^

::

    Usage: rtxmlrpc [options] <method> <args>...

    Perform raw rTorrent XMLRPC calls, like "rtxmlrpc throttle.up.rate ''".
    Start arguments with "+" or "-" to indicate they're numbers (type i4 or i8).

    For more details, see the full documentation at

        https://pyrocore.readthedocs.io/

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -q, --quiet           omit informational logging
      -v, --verbose         increase informational logging
      --debug               always show stack-traces for errors
      --cron                run in cron mode (with different logging configuration)
      --config-dir=DIR      configuration directory [~/.pyroscope]
      --config-file=PATH    additional config file(s) to read
      -D KEY=VAL [-D ...], --define=KEY=VAL [-D ...]
                            override configuration attributes
      -r, --repr            show Python pretty-printed response
      -x, --xml             show XML response
      -i, --as-import       execute each argument as a private command using 'import'
