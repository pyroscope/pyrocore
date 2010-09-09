#! /bin/bash
#
# CONCURRENT HASHING TEST SCRIPT
#

# Do a self-referential listing for piping to pastee
cat $0; echo; echo "~~~ Start of test run ~~~"

# Preparation
cd $(dirname $(dirname $0))
test ! -f fifotest.torrent || rm fifotest.torrent
test ! -e fifotest.fifo || rm fifotest.fifo
mkfifo fifotest.fifo

# Start hashing process
mktor -r concurrent -o fifotest fifotest.fifo OBT -v 2>&1 | sed -e s:$HOME:~: &

# Start filename emitting process (fake .25 sec latency)
( for file in $(find tests/ -name "*.py"); do
    echo >&2 "$(date -u +'%T.%N') $file is complete!"
    echo $file
    sleep .25
done ) >fifotest.fifo &

# Wait for hashing to complete
while test ! -f fifotest.torrent; do
    echo "$(date -u +'%T.%N') Waiting for metafile..."
    sleep .1
done
echo

# Show the result
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
lstor -q fifotest.torrent

# Clean up
rm fifotest.*
