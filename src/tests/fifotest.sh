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
mktor -r concurrent -o fifotest.torrent fifotest.fifo announce -v &

# Start filename emitting process
( for file in $(find tests/ -name "*.py"); do
    echo >&2 "$file is complete!"
    echo $file
    sleep .25
done ) >fifotest.fifo &

# Wait for hashing to complete
while test ! -f fifotest.torrent; do
    echo "Waiting for metafile..."
    sleep .1
done
echo

# Show the result
lstor -q fifotest.torrent

# Clean up
rm fifotest.*
