#! /bin/bash
#
# rTorrent startup script
#

RT_BINDIR="{{ rtorrent_bindir }}"
RT_OPTS=( )
RT_OPTS+=( -D -I )  # comment this to get deprecated commands

if [ "$TERM" = "${TERM%-256color}" ]; then
    export TERM="$TERM-256color"
fi

export LANG=en_US.UTF-8
umask 0027

builtin cd $(dirname $0)
export RT_HOME="$PWD"
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

"$RT_BIN" "${RT_OPTS[@]}"
