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
PROJECT_ROOT="$(command cd $(dirname "$0") >/dev/null && pwd)"
command cd "$PROJECT_ROOT" >/dev/null
echo "Installing into $PWD..."
rtfm="DO read http://code.google.com/p/pyroscope/wiki/InstallFromSource."

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
assert sys.version_info >= (2, 5), "Use Python 2.5 or a higher 2.X! Read the wiki."
assert sys.version_info < (3,), "Use Python 2.5, 2.6, or 2.7! Read the wiki."
.

echo "Updating your installation..."

# Bootstrap if script was downloaded...
if test -d .git; then
    git pull --ff-only
else
    git clone "https://github.com/pyroscope/pyrocore.git" pyroscope
    cd pyroscope
fi
. "$PROJECT_ROOT/util.sh" # load funcs

# Ensure virtualenv is there
test -f bin/activate || install_venv --never-download

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
test ! -d ${BIN_DIR:-~/bin} || ln -nfs $(grep -l 'entry_point.*pyrocore.*console_scripts' $PWD/bin/*) ${BIN_DIR:-~/bin}/
test ! -d ${BIN_DIR:-~/bin} || ln -nfs $PWD/bin/python-pyrocore ${BIN_DIR:-~/bin}/

# Update config defaults
./bin/pyroadmin --create-config

# Make sure PATH is decent
( echo $PATH | tr : \\n | egrep "^$HOME/bin/?\$" >/dev/null ) || echo "$HOME/bin is NOT on your PATH, you need to fix that"'!'
