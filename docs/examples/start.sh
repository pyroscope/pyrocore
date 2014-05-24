#! /bin/bash
#
# rTorrent startup script
#
if [ "$TERM" = "${TERM%-256color}" ]; then
    export TERM="$TERM-256color"
fi
export LANG=en_US.UTF-8
umask 0027
cd $(dirname $0)
export RT_SOCKET=$PWD/.scgi_local
test -S $RT_SOCKET && lsof $RT_SOCKET >/dev/null && { echo "rTorrent already running"; exit 1; }
test ! -e $RT_SOCKET || rm $RT_SOCKET

_at_exit() {
    test -z "$TMUX" || tmux set-w automatic-rename on >/dev/null
    stty sane
    test ! -e $RT_SOCKET || rm $RT_SOCKET
}
trap _at_exit INT TERM EXIT
test -z "$TMUX" || tmux rename-w rT-PS

rtorrent -n -o import=$PWD/rtorrent.rc
