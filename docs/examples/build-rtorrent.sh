#! /bin/bash
#
# Build rTorrent including patches
#
export LT_VERSION=0.12.6
export RT_VERSION=0.8.6
export CARES_VERSION=1.7.3
export CURL_VERSION=7.21.1
export XMLRPC_REV=2122

#
# HERE BE DRAGONS!
#
export INST_DIR="$HOME/lib/rtorrent-$RT_VERSION"
export CFLAGS="-I $INST_DIR/include"
export CXXFLAGS="$CFLAGS"
export LDFLAGS="-L$INST_DIR/lib"
export PKG_CONFIG_PATH="$INST_DIR/lib/pkgconfig"

XMLRPC_URL="https://xmlrpc-c.svn.sourceforge.net/svnroot/xmlrpc-c/advanced@$XMLRPC_REV"
TARBALLS=$(cat <<.
http://c-ares.haxx.se/c-ares-$CARES_VERSION.tar.gz
http://curl.haxx.se/download/curl-$CURL_VERSION.tar.gz
http://libtorrent.rakshasa.no/downloads/libtorrent-$LT_VERSION.tar.gz
http://libtorrent.rakshasa.no/downloads/rtorrent-$RT_VERSION.tar.gz
.
)

export SRC_DIR=$(cd $(dirname $0) && pwd)
SUBDIRS="c-ares-*[0-9] curl-*[0-9] xmlrpc-c-advanced libtorrent-*[0-9] rtorrent-*[0-9]"

set -e
set +x


#
# HELPERS
#
prep() { # Create directories
    mkdir -p $INST_DIR/{bin,include,lib,man,share}
}

download() { # Download & unpack sources
    test -d xmlrpc-c-advanced || ( echo "Getting xmlrpc-c" && svn -q checkout "$XMLRPC_URL" xmlrpc-c-advanced )
    for url in $TARBALLS; do
        url_base=${url##*/}
        test -f ${url_base} || ( echo "Getting $url_base" && wget -q $url )
        test -d ${url_base%.tar.gz} || ( echo "Unpacking ${url_base}" && tar xfz ${url_base} )
    done
}

build() { # Build and install all components
    ( cd c-ares-*[0-9] && ./configure && make && make prefix=$INST_DIR install )
    sed -ie s:/usr/local:$INST_DIR: $INST_DIR/lib/pkgconfig/*.pc $INST_DIR/lib/*.la
    ( cd curl-*[0-9] && ./configure --enable-ares && make && make prefix=$INST_DIR install )
    sed -ie s:/usr/local:$INST_DIR: $INST_DIR/lib/pkgconfig/*.pc $INST_DIR/lib/*.la 
    ( cd xmlrpc-c-advanced && ./configure --with-libwww-ssl && make && make install PREFIX=$INST_DIR )
    sed -ie s:/usr/local:$INST_DIR: $INST_DIR/bin/xmlrpc-c-config
    ( cd libtorrent-*[0-9] && ./configure && make && make prefix=$INST_DIR install )
    sed -ie s:/usr/local:$INST_DIR: $INST_DIR/lib/pkgconfig/*.pc $INST_DIR/lib/*.la 
    ( cd rtorrent-*[0-9] && ./configure --with-xmlrpc-c=$INST_DIR/bin/xmlrpc-c-config && make && make prefix=$INST_DIR install )

    mkdir -p ~/bin
    ln -nfs $INST_DIR/bin/rtorrent ~/bin/rtorrent-$RT_VERSION
    ln -nfs rtorrent-$RT_VERSION ~/bin/rtorrent
}

clean() { # Clean up generated files
    for i in $SUBDIRS; do
        ( cd $i && make clean )
    done
}

clean_all() { # Remove all downloads and created files
    rm *.tar.gz >/dev/null || :
    for i in $SUBDIRS; do
        test ! -d $i || rm -rf $i >/dev/null
    done
}

check() { # Print some diagnostic success indicators
    echo
    echo -n "Check that static linking worked: "
    libs=$(ldd $INST_DIR/bin/rtorrent | egrep "lib(cares|curl|xmlrpc|torrent)")
    test -n $(echo "$libs" | grep -v "$INST_DIR") && echo OK || echo FAIL
    echo "$libs"
}


#
# MAIN
#
case "$1" in
    all)        download; prep; build; check ;;
    clean)      clean ;;
    clean_all)  clean_all ;; 
    download)   download ;;
    build)      prep; build; check ;;
    check)      check ;;
    *)
        echo >&2 "Usage: $0 (all | clean | clean_all | download | build | check)"
        exit 1
        ;;
esac

