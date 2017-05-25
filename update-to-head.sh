#! /bin/bash
git_projects="pyrobase auvyon"

# Find most suitable Python
echo "~~~ On errors, paste EVERYTHING below ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
deactivate 2>/dev/null
PYTHON="$1"
test -z "$PYTHON" -a -x "/usr/bin/python2" && PYTHON="/usr/bin/python2"
test -z "$PYTHON" -a -x "/usr/bin/python" && PYTHON="/usr/bin/python"
test -z "$PYTHON" && PYTHON="python"

set -e
MY_SUM=$(md5sum "$0" | cut -f1 -d' ')
PROJECT_ROOT="$(command cd $(dirname "$0") >/dev/null && pwd)"
command cd "$PROJECT_ROOT" >/dev/null
echo "Installing into $PWD..."
rtfm="DO read 'https://pyrocore.readthedocs.io/en/latest/installation.html'."

# Fix Generation YouTube's reading disability
for cmd in $PYTHON git; do
    which $cmd >/dev/null 2>&1 || { echo >&2 "You need a working '$cmd' on your PATH. $rtfm"; exit 1; }
done

# People never read docs anyway, so let the machine check...
test $(id -u) -ne 0 || { echo "Do NOT install as root! $rtfm"; exit 1; }
test -f ./bin/activate && vpy=$PWD/bin/python || vpy=$PYTHON
cat <<'.' | $vpy
import sys
print("Using Python %s" % sys.version)
assert sys.version_info >= (2, 6), "Use Python 2.6 or 2.7! Read the docs."
assert sys.version_info < (3,), "Use Python 2.6 or 2.7! Read the docs."
.

echo "Updating your installation..."

# Bootstrap if script was downloaded...
if test -d .git; then
    git pull --ff-only
else
    git clone "https://github.com/pyroscope/pyrocore.git" tmp
    mv tmp/???* tmp/.??* .; rmdir tmp
    MY_SUM="let's start over"
fi

if test "$MY_SUM" != $(md5sum "$0" | cut -f1 -d' '); then
    echo -e "\n\n*** Update script changed, starting over ***\n"
    exec "$0" "$@"
fi

. "$PROJECT_ROOT/util.sh" # load funcs

# Ensure virtualenv is there
test -f bin/activate || install_venv --never-download
update_venv ./bin/pip

# Get base packages initially, for old or yet incomplete installations
for project in $git_projects; do
    test -d $project || { echo "Getting $project..."; git clone "git://github.com/pyroscope/$project.git" $project; }
done

# Update source
source bin/activate
for project in $git_projects; do
    ( builtin cd $project && git pull -q --ff-only )
done
source bootstrap.sh
for project in $git_projects; do
    ( builtin cd $project && ../bin/paver -q develop -U )
done

# Register new executables
ln -nfs python ./bin/python-pyrocore
test ! -d ${BIN_DIR:-~/bin} || \
    ln -nfs $(egrep -l '(from.pyrocore.scripts|entry_point.*pyrocore.*console_scripts)' $PWD/bin/*) ${BIN_DIR:-~/bin}/
test ! -d ${BIN_DIR:-~/bin} || ln -nfs $PWD/bin/python-pyrocore ${BIN_DIR:-~/bin}/

# Make sure people update their main config
rm -f "$PROJECT_ROOT/src/pyrocore/data/config"/rtorrent-0.8.?.rc 2>/dev/null || :
rm -f "$HOME/.pyroscope"/rtorrent-0.8.?.rc.default 2>/dev/null || :

# Update config defaults
rm -f "$HOME/.pyroscope/rtorrent.d.rc" 2>/dev/null || :
rm -f "$HOME/.pyroscope/rtorrent.d"/view-zz-collapse.rc* 2>/dev/null || :
./bin/pyroadmin --create-config
./bin/pyroadmin --create-import "~/.pyroscope/rtorrent.d/*.rc.default"

# Relocate to ~/.local
test "$PROJECT_ROOT" != "$HOME/lib/pyroscope" || cat <<'EOF'

*****************************************************************************
The default install location has changed, consider moving to the new path at
'~/.local/pyroscope'!

Call these commands:

    mkdir -p ~/.local/pyroscope
    cp -p ~/lib/pyroscope/update-to-head.sh ~/.local/pyroscope
    ~/.local/pyroscope/update-to-head.sh

*****************************************************************************

EOF

# Make sure PATH is decent
( echo $PATH | tr : \\n | egrep "^$HOME/bin/?\$" >/dev/null ) || echo "$HOME/bin is NOT on your PATH, you need to fix that"'!'
