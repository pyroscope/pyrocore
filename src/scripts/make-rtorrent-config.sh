#! /usr/bin/env bash
#
# Create rTorrent config using mostly pimp-my-box snippets
#

export RT_HOME="${RT_HOME:-$HOME/rtorrent}"

# This can be used to test changes contained in a 'pimp-my-box' workdir
PMB_ROOT_DIR="$1"

INSTALL_ROOT="$(command cd $(dirname "$0") >/dev/null && pwd)"
INSTALL_ROOT="$(dirname $(dirname "$INSTALL_ROOT"))"

mkdir -p "$RT_HOME"
command cd "$RT_HOME"

# Create "rtorrent.rc"
echo "*** Creating 'rtorrent.rc' in '$RT_HOME'..."
sed -e "s:RT_HOME:$RT_HOME:" <"$INSTALL_ROOT/docs/examples/rtorrent.rc" >"$RT_HOME/rtorrent.rc"

# Get pimp-my-box source
if test -n "$PMB_ROOT_DIR" -a -d "$PMB_ROOT_DIR"; then
    echo "*** Copying 'rtorrent.d' snippets..."
    mkdir -p "rtorrent.d"
    cp -p "$PMB_ROOT_DIR/roles/rtorrent-ps/templates/rtorrent/rtorrent.d"/*.rc "rtorrent.d"
else
    echo "*** Downloading 'rtorrent.d' snippets..."
    curl -L -o /tmp/$USER-pimp-my-box.tgz \
        "https://github.com/pyroscope/pimp-my-box/archive/master.tar.gz"
    tar -xz --strip-components=5 -f /tmp/$USER-pimp-my-box.tgz \
        "pimp-my-box-master/roles/rtorrent-ps/templates/rtorrent/rtorrent.d"
fi

if test ! -f ~/bin/_event.download.finished; then
    echo -e >~/bin/_event.download.finished '#/bin/bash\necho "$@"'
    chmod a+rx ~/bin/_event.download.finished
fi

# Replace Ansible variables
echo "*** Configuring 'rtorrent.d' snippets..."
( command cd rtorrent.d && for i in *.rc; do \
    sed -i -re 's/\{\{ item }}/'"$i/" -e '/^# !.+!$/d' "$i" \
            -e 's:~/rtorrent/:'"$RT_HOME/:" -e "s:'rtorrent' user:'$USER' user:"; \
  done )
sed -i -re 's/\{\{ inventory_hostname }}/'"$(hostname)/" rtorrent.d/20-session-name.rc
sed -i -r \
    -e 's/\{\{ rt_pieces_memory }}/1200M/' \
    -e 's/\{\{ rt_xmlrpc_size_limit }}/16M/' \
    -e 's/\{\{ rt_global_up_rate_kb }}/115000/' \
    -e 's/\{\{ rt_global_down_rate_kb }}/115000/' \
    -e 's/\{\{ .+rt_system_umask.+ }}/0027/' \
    -e 's/\{\{ rt_keys_layout }}/qwerty/' \
    rtorrent.d/20-host-var-settings.rc

# Check that there are no overlooked Ansible variables
echo
echo "*****************************************************************************"

if egrep -m1 '\{\{.+?}}' rtorrent.d/*.rc >/dev/null; then
    echo "Check the following output, you need to insert your own settings everywhere"
    echo "a '{{ ... }}' placeholder appears!"
    echo

    egrep -nH --color=yes '\{\{.+?}}' rtorrent.d/*.rc
else
    echo "Your configuration is ready."
    echo
    ls -lR rtorrent.rc rtorrent.d/*.rc
fi

# END of "make-rtorrent-config.sh"
