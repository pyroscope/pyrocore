#! /bin/bash
cat $0; echo
cd $(dirname $(dirname $0))

test ! -f fifotest.torrent || rm fifotest.torrent
test ! -e fifotest.fifo || rm fifotest.fifo
mkfifo fifotest.fifo

mktor -r incremental -o fifotest.torrent fifotest.fifo announce -v &

( for file in $(find tests/ -name "*.py"); do
    echo >&2 "$file is complete!"
    echo $file
    sleep .25
done ) >fifotest.fifo &
 
while test ! -f fifotest.torrent; do
    echo "Waiting for metafile..."
    sleep .1
done
echo
lstor -q fifotest.torrent

rm fifotest.*
