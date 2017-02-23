Querying system information
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``rtuptime`` script shows you essential information about your
*rTorrent* instance:

.. code-block:: shell

    #! /bin/bash
    SCGI_SOCKET=~/rtorrent/.scgi_local

    if test ! -S $SCGI_SOCKET; then
        echo >&2 "rTorrent is not running (no socket $SCGI_SOCKET)"
        exit 1
    fi

    echo -n rTorrent $(rtxmlrpc system.client_version)/$(rtxmlrpc system.library_version)
    echo -n , up $(rtxmlrpc to_elapsed_time $(ls -l --time-style '+%s' $SCGI_SOCKET | awk '{print $6}'))
    echo -n \ [$(rtcontrol -qo"1 %(uploaded)s %(size)s" \* | \
        awk '{ TOT += $1; UP += $2; SUM += $3} END { print TOT " loaded; U: " UP/1024/1024/1024 " GiB; S: " SUM/1024/1024/1024 }') GiB]
    echo -n , D: $(rtxmlrpc to_xb $(rtxmlrpc throttle.global_down.total))
    echo -n \ @ $(rtxmlrpc to_xb $(rtxmlrpc throttle.global_down.rate))/s
    echo -n \ of $(rtxmlrpc to_xb $(rtxmlrpc throttle.global_down.max_rate))/s
    echo -n , U: $(rtxmlrpc to_xb $(rtxmlrpc throttle.global_up.total))
    echo -n \ @ $(rtxmlrpc to_xb $(rtxmlrpc throttle.global_up.rate))/s
    echo -n \ of $(rtxmlrpc to_xb $(rtxmlrpc throttle.global_up.max_rate))/s
    echo

When called, it prints something like this:

.. code-block:: shell

    $ rtuptime
    rTorrent 0.9.6/0.13.6, up 189:00:28 [315 loaded; U: 177.292 GiB; S: 891.781 GiB],
    D: 27.3 GB @ 0.0 KB/s of 520.0 KB/s, U: 36.8 MB @ 0.0 KB/s of 52.0 KB/s

And yes, doing the same in a :ref:`Python script <scripts>`
would be much more CPU efficient. ;)

If you connect via ``network.scgi.open_port``, touch a file in ``/tmp`` in your
startup script and use that for uptime checking.


General maintenance tasks
^^^^^^^^^^^^^^^^^^^^^^^^^

Here are some commands that can help with managing your rTorrent
instance:

.. code-block:: shell

    # Flush ALL session data NOW, use this before you make a backup of your session directory
    rtxmlrpc session.save


Setting and checking throttles
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To set the speed of the ``slow`` throttle, and then check your new limit
and print the current download rate, use:

.. code-block:: shell

    rtxmlrpc throttle.down '' slow 120
    # 0
    rtxmlrpc throttle.down.max '' slow
    # 122880
    rtxmlrpc throttle.down.rate '' slow
    # 0

Note that the speed is specified in KiB/s as a string when setting it
but returned in bytes/s as an integer on queries.

The following script makes this available in an easy usable form, e.g.
``throttle slow 42`` – it also shows the current rate and settings of
all defined throttles when called without arguments:

.. code-block:: shell

    #! /bin/bash
    # Set speed of named throttle

    #
    # CONFIGURATION
    #
    throttle_name="seed" # default name
    unit=1024 # KiB/s

    #
    # HERE BE DRAGONS!
    #
    down=false
    if test "$1" = "-d"; then
        down=true
        shift
    fi

    if test -n "$(echo $1 | tr -d 0-9)"; then
        # Non-numeric $1 is a name
        throttle_name=$1
        shift
    fi

    if test -z "$1"; then
        echo >&2 "Usage: ${0/$HOME/~} [-d] [<throttle-name=$throttle_name>] <rate>"

        rtorrent_rc=~/.rtorrent.rc
        test -e "$rtorrent_rc" || rtorrent_rc="$(rtxmlrpc system.get_cwd)/rtorrent.rc"
        if test -e "$rtorrent_rc"; then
            throttles="$(egrep '^throttle[._](up|down)' $rtorrent_rc | tr ._=, ' ' | cut -f3 -d" " | sort | uniq)"
            echo
            echo "CURRENT THROTTLE SETTINGS"
            for throttle in $throttles; do
                echo -e "  $throttle\t" \
                    "U: $(rtxmlrpc to_kb $(rtxmlrpc throttle.up.rate $throttle)) /" \
                    "$(rtxmlrpc to_kb $(rtxmlrpc throttle.up.max $throttle | sed 's/^-1$/0/')) KiB/s\t" \
                    "D: $(rtxmlrpc to_kb $(rtxmlrpc throttle.down.rate $throttle)) /" \
                    "$(rtxmlrpc to_kb $(rtxmlrpc throttle.down.max $throttle | sed 's/^-1$/0/')) KiB/s"
            done
        fi
        exit 2
    fi

    rate=$(( $1 * $unit ))

    # Set chosen bandwidth
    if $down; then
        if test $(rtxmlrpc throttle.down.max $throttle_name) -ne $rate; then
            rtxmlrpc -q throttle.down $throttle_name $(( $rate / 1024 ))
            echo "Throttle '$throttle_name' download rate changed to" \
                 "$(( $(rtxmlrpc throttle.down.max $throttle_name) / 1024 )) KiB/s"
        fi
    else
        if test $(rtxmlrpc throttle.up.max $throttle_name) -ne $rate; then
            rtxmlrpc -q throttle.up $throttle_name $(( $rate / 1024 ))
            echo "Throttle '$throttle_name' upload rate changed to" \
                 "$(( $(rtxmlrpc throttle.up.max $throttle_name) / 1024 )) KiB/s"
        fi
    fi


Global throttling when other computers are up
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to be loved by your house-mates, try this:

.. code-block:: shell

    #! /bin/bash
    # Throttle bittorrent when certain hosts are up

    #
    # CONFIGURATION
    #
    hosts_to_check="${1:-mom dad}"
    full_up=62
    full_down=620
    nice_up=42
    nice_down=123
    unit=1024 # KiB/s

    #
    # HERE BE DRAGONS!
    #

    # Check if any prioritized hosts are up
    up=$(( $full_up * $unit ))
    down=$(( $full_down * $unit ))
    hosts=""

    for host in $hosts_to_check; do
        if ping -c1 $host >/dev/null 2>&1; then
            up=$(( $nice_up * $unit ))
            down=$(( $nice_down * $unit ))
            hosts="$hosts $host"
        fi
    done

    reason="at full throttle"
    test -z "$hosts" || reason="for$hosts"

    # Set chosen bandwidth
    if test $(rtxmlrpc throttle.global_up.max_rate) -ne $up; then
        echo "Setting upload rate to $(( $up / 1024 )) KiB/s $reason"
        rtxmlrpc -q throttle.global_up.max_rate.set_kb $(( $up / 1024 ))
    fi
    if test $(rtxmlrpc throttle.global_down.max_rate) -ne $down; then
        echo "Setting download rate to $(( $down / 1024 )) KiB/s $reason"
        rtxmlrpc -q throttle.global_down.max_rate.set_kb $(( $down / 1024 ))
    fi


Add it to your crontab and run it every few minutes.


Throttling rTorrent for a limited time
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to slow down *rTorrent* to use your available bandwidth on
foreground tasks like browsing, but usually forget to return the throttle
settings back to normal, then you can use the provided `rt-backseat`_ script.
It will register a job via ``at``, so that command must be installed on
the machine for it to work. The default throttle speed and timeout can be
set at the top of the script.

.. _`rt-backseat`:
    https://github.com/pyroscope/pyrocore/blob/master/docs/examples/rt-backseat
