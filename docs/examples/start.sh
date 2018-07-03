#!/usr/bin/env bash
#
# rTorrent startup script
#

NOCRON_DELAY=600
RT_BINDIR="{{ rtorrent_bindir }}"
RT_OPTS=( )
RT_OPTS+=( -D -I )  # comment this to get deprecated commands

builtin cd "$(dirname "$0")"
export RT_HOME="$(pwd -P)"

fail() {
    echo "ERROR:" "$@"
    exit 1
}

# Performa a mount check
#test -f "$RT_HOME/work/.mounted" -a -f "$RT_HOME/done/.mounted" \
#    || fail "Data drive(s) not mounted!"


if [ "$TERM" = "${TERM%-256color}" ]; then
    export TERM="$TERM-256color"
fi

export LANG=en_US.UTF-8
umask 0027

RT_OPTS+=( -n -o "import=$RT_HOME/rtorrent.rc" )

export RT_SOCKET=$PWD/.scgi_local
test -S $RT_SOCKET && lsof $RT_SOCKET >/dev/null && { echo "rTorrent already running"; exit 1; }
test ! -e $RT_SOCKET || rm $RT_SOCKET

_at_exit() {
    test -z "$TMUX" || tmux set-w automatic-rename on >/dev/null
    stty sane
    test ! -e $RT_SOCKET || rm $RT_SOCKET
}
trap _at_exit INT TERM EXIT
test -z "$TMUX" || tmux 'rename-w' 'rT-PS'

if test -n "$RT_BINDIR"; then
    RT_BINDIR="${RT_BINDIR%/}/"

    # Try usual suspects if config is wrong
    test -x "${RT_BINDIR}rtorrent" || RT_BINDIR="$HOME/bin/"
    test -x "${RT_BINDIR}rtorrent" || RT_BINDIR="/opt/rtorrent/bin/"
    test -x "${RT_BINDIR}rtorrent" || RT_BINDIR="/usr/local/bin/"
    test -x "${RT_BINDIR}rtorrent" || RT_BINDIR="/usr/bin/"
    test -x "${RT_BINDIR}rtorrent" || RT_BINDIR=""
fi
#RT_BINDIR="$HOME/src/rtorrent-ps/rtorrent-0.9.6/src/"
export RT_BIN="${RT_BINDIR}rtorrent"

if which objdump >/dev/null; then
    RUNPATH=$(objdump -x "$RT_BIN" | grep RPATH | sed -re 's/ *RPATH *//')
    test -n "$RUNPATH" || RUNPATH=$(objdump -x "$RT_BIN" | grep RUNPATH | sed -re 's/ *RUNPATH *//')
    test -z "$RUNPATH" || LD_LIBRARY_PATH="$RUNPATH${LD_LIBRARY_PATH:+:}${LD_LIBRARY_PATH}"
fi

# Stop cron jobs during startup, unless already stopped
rm "$RT_HOME/rtorrent.d/START-NOCRON.rc" 2>/dev/null || :
nocron_delay=''
if test -d "$RT_HOME/rtorrent.d" -a ! -f "~/NOCRON"; then
    nocron_delay=$(( $(date +'%s') + $NOCRON_DELAY ))
    echo >"$RT_HOME/rtorrent.d/START-NOCRON.rc" \
          "schedule2 = nocron_during_startup, $NOCRON_DELAY, 0, \"execute.nothrow=rm,$HOME/NOCRON\""
    touch "$HOME/NOCRON"
fi

"$RT_BIN" "${RT_OPTS[@]}" ; RC=$?
test -z "$nocron_delay" -o "$(date +'%s')" -ge "${nocron_delay:-0}" || rm "$HOME/NOCRON" 2>/dev/null || :
exit $RC
