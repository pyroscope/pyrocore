# library of helper functions (needs to be sourced)

abend() {
    echo
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo -n >&2 "ERROR: "
    for i in "$@"; do
        echo >&2 "$i"
    done
    set +e
    return 1
}

fail() {
    abend "$@"
    exit 1
}


SCRIPTNAME="$0"
test "$SCRIPTNAME" != "-bash" -a "$SCRIPTNAME" != "-/bin/bash" || SCRIPTNAME="${BASH_SOURCE[0]}"

test -f "$PROJECT_ROOT/util.sh" || unset PROJECT_ROOT
PROJECT_ROOT=${PROJECT_ROOT:-$(builtin cd $(dirname "$SCRIPTNAME") >/dev/null && pwd)}
test -f "$PROJECT_ROOT/util.sh" || PROJECT_ROOT=$(dirname "$PROJECT_ROOT")
test -f "$PROJECT_ROOT/util.sh" || abend "Cannot find project root in '$PROJECT_ROOT'"
export PROJECT_ROOT


fix_wrappers() {
    # Ensure unversioned wrappers exist
    for i in "$PROJECT_ROOT"/bin/*-2.*; do
        tool=${i%-*}
        test -x "$tool" || ln -s $(basename "$i") "$tool"
    done
}

ensure_pip() {
    test -x "$PROJECT_ROOT"/bin/pip || "$PROJECT_ROOT"/bin/easy_install -q pip
    test -x "$PROJECT_ROOT"/bin/pip || fix_wrappers
    test -x "$PROJECT_ROOT"/bin/pip || abend "installing pip into $PROJECT_ROOT failed"
}

update_venv() {
    local pip="${1:?You MUST pass a pip executable}"

    $pip install -U pip
    $pip install -U setuptools || :
    $pip install -U wheel || :
}

install_venv() {
    venv_url="https://pypi.python.org/packages/d4/0c/9840c08189e030873387a73b90ada981885010dd9aea134d6de30cd24cb8/virtualenv-15.1.0.tar.gz"
    mkdir -p "$PROJECT_ROOT/lib"
    test -f "$PROJECT_ROOT/lib/virtualenv.tgz" || \
        $PYTHON -c "import urllib2; open('$PROJECT_ROOT/lib/virtualenv.tgz','w').write(urllib2.urlopen('$venv_url').read())"
    test -d "$PROJECT_ROOT/lib/virtualenv" || \
        ( mkdir -p lib/virtualenv && cd lib/virtualenv && tar -xz -f ../virtualenv.tgz --strip-components=1 )
    deactivate 2>/dev/null || true
    $PYTHON "$PROJECT_ROOT"/lib/virtualenv/virtualenv.py "$@" "$PROJECT_ROOT"
    test -f "$PROJECT_ROOT"/bin/activate || abend "creating venv in $PROJECT_ROOT failed"

    ensure_pip
}

pip_install_opt() {
    ensure_pip
    "$PROJECT_ROOT"/bin/pip install "$@"
    fix_wrappers
}

pip_install() {
    ensure_pip
    "$PROJECT_ROOT"/bin/pip install "$@" || abend "'pip install $@' failed"
    fix_wrappers
}
