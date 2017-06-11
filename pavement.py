# -*- coding: utf-8 -*-
""" PyroCore - Python Torrent Tools Core Package.

    This project provides a collection of tools for the BitTorrent protocol
    and especially the `rTorrent client`_. They enable you to filter
    rTorrent's item list for displaying or changing selected items, also
    creating, inspecting and changing ``.torrent`` files, and much more.

    An optional daemon process (``pyrotorque``) can add flexible queue
    management for rTorrent, starting items added in bulk slowly over time
    according to customizable rules. The same daemon can also watch one or
    more directory trees recursively for new metafiles using inotify,
    resulting in instantaneous loading without any polling and no extra
    configuration for nested directories.

    The ``PyroScope`` command line utilities are *not* the same as the
    sibling project `rTorrent-PS`_, and they work perfectly fine without it;
    the same is true the other way 'round. It's just that both
    unsurprisingly have synergies if used together, and some features *do*
    only work when both are present.

    Further information can be found in the `main documentation`_.

    To get in contact and share your experiences with other users of *PyroScope*,
    join the `pyroscope-users`_ mailing list or the inofficial ``##rtorrent``
    channel on ``irc.freenode.net``.

    .. _rTorrent client: https://github.com/rakshasa/rtorrent
    .. _rTorrent-PS: https://github.com/pyroscope/rtorrent-ps
    .. _main documentation: http://pyrocore.readthedocs.io/
    .. _pyroscope-users: http://groups.google.com/group/pyroscope-users

    Copyright (c) 2009 - 2017 The PyroScope Project <pyroscope.project@gmail.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
from __future__ import with_statement

import os
import re
import sys
import glob
import time
import subprocess
import webbrowser

from paver.easy import *
from paver.setuputils import setup

try:
    from pyrobase.paver.easy import *
except ImportError:
    pass # dependencies not yet installed

from setuptools import find_packages


SPHINX_AUTOBUILD_PORT = 8340


#
# Project Metadata
#

changelog = path("debian/changelog")
if not changelog.exists():
    changelog = path("../debian/changelog")

name, version = open(changelog).readline().split(" (", 1)
version, _ = version.split(")", 1)

project = Bunch(
    # egg
    name = "pyrocore",
    version = version,
    package_dir = {"": "src"},
    packages = find_packages("src", exclude = ["tests"]),
    entry_points = {
        "console_scripts": [
            "chtor = pyrocore.scripts.chtor:run",
            "hashcheck = pyrocore.scripts.hashcheck:run",
            "lstor = pyrocore.scripts.lstor:run",
            "mktor = pyrocore.scripts.mktor:run",
            "pyroadmin = pyrocore.scripts.pyroadmin:run",
            "rtcontrol = pyrocore.scripts.rtcontrol:run",
            "rtevent = pyrocore.scripts.rtevent:run",
            "rtmv = pyrocore.scripts.rtmv:run",
            "rtxmlrpc = pyrocore.scripts.rtxmlrpc:run",
            "pyrotorque = pyrocore.scripts.pyrotorque:run",
            # "rtorrd = pyrocore.scripts.rtorrd:run",
        ],
    },
    include_package_data = True,
    zip_safe = False,
    data_files = [
        ("EGG-INFO", [
            "README.md", "LICENSE", "debian/changelog",
        ]),
    ],

    # dependencies
    setup_requires = [
    ],
    install_requires = [
        "pyrobase>=0.2",
        "ProxyTypes>=0.9",
    ],
    extras_require = {
        "templating": ["Tempita>=0.5.1"],
        "pyrotorque": ["APScheduler>=2.0.2,<3"],
        "pyrotorque.httpd": ["waitress>=0.8.2", "WebOb>=1.2.3", "psutil>=0.6.1"],
        "FlexGet": ["flexget>=1.0"],
    },

    # tests
    test_suite = "nose.collector",

    # cheeseshop
    author = "The PyroScope Project",
    author_email = "pyroscope.project@gmail.com",
    description = __doc__.split('.', 1)[0].strip(),
    long_description = __doc__.split('.', 1)[1].strip(),
    license = [line.strip() for line in __doc__.splitlines()
        if line.strip().startswith("Copyright")][0],
    url = "https://github.com/pyroscope/pyrocore",
    keywords = "bittorrent rtorrent cli python",
    classifiers = [
        # see http://pypi.python.org/pypi?:action=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.7",
        "Topic :: Communications :: File Sharing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)

options(
    setup=project,
    docs=Bunch(docs_dir="docs/apidocs", includes="pyrobase"),
)


#
# Build
#
@task
@needs(["setuptools.command.egg_info"])
def bootstrap():
    "initialize project"
    # Link files shared by subprojects
    debian = path("debian")
    debian.exists() or debian.makedirs()

    for shared in ("debian/changelog", "LICENSE"):
        path(shared).exists() or (path("..") / shared).link(shared)

    build()


@task
def build():
    "build the software"
    #rtrc_086 = path("src/pyrocore/data/config/rtorrent-0.8.6.rc")
    #rtrc_089 = path(str(rtrc_086).replace("0.8.6", "0.8.9"))
    #if not rtrc_089.exists() or rtrc_086.mtime > rtrc_089.mtime:
    #    rtrc_089.write_bytes(rtrc_086.text().replace("#087#", ""))
    #    sh("./src/scripts/migrate_rtorrent_rc.sh %s >/dev/null" % rtrc_089)
    #    sh("bash -c 'rm %s{?0.8.6,-????-??-??-??-??-??}'" % rtrc_089)

    call_task("setuptools.command.build")


@task
def gendocs():
    "create some doc pages automatically"
    helppage = path("docs/references-cli-usage.rst")
    content = [
        ".. automatically generated using 'paver gendocs'.",
        "",
        ".. contents::",
        "    :local:",
        "",
        ".. note::",
        "",
        "    The help output presented here applies to version ``%s`` of the tools."
            % sh("pyroadmin --version", capture=True).split()[1],
        "",
    ]

    for tool in sorted(project.entry_points["console_scripts"]):
        tool, _ = tool.split(None, 1)
        content.extend([
            ".. _cli-usage-%s:" % tool,
            "",
            tool,
            '^' * len(tool),
            "",
            "::",
            "",
        ])
        help_opt = "--help-fields --config-dir /tmp" if tool == "rtcontrol" else "--help"
        help_txt = sh("%s -q %s" % (tool, help_opt), capture=True, ignore_error=True).splitlines()
        content.extend('    ' + i for i in help_txt)
        content.extend([
            "",
        ])

    content = [line.rstrip() for line in content if all(
        i not in line for i in (", Copyright (c) ", "Total time: ", "Configuration file '/tmp/")
    )]
    content = [line for line, succ in zip(content, content[1:] + ['']) if line or succ] # filter twin empty lines
    helppage.write_lines(content)


@task
def dist_docs():
    "create a documentation bundle"
    dist_dir = path("dist")
    html_dir = path("docs/_build/html")
    docs_package = path("%s/%s-%s-docs.zip" % (dist_dir.abspath(), options.setup.name, options.setup.version))

    if not html_dir.exists():
        error("\n*** ERROR: Please build the HTML docs!")
        sys.exit(1)

    dist_dir.exists() or dist_dir.makedirs()
    docs_package.exists() and docs_package.remove()

    sh(r'cd %s && find . -type f \! \( -path "*/.svn*" -o -name "*~" \) | sort'
       ' | zip -qr -@ %s' % (html_dir, docs_package,))

    print
    print "Upload @ http://pypi.python.org/pypi?:action=pkg_edit&name=%s" % ( options.setup.name,)
    print docs_package


def watchdog_pid():
    """Get watchdog PID via ``netstat``."""
    result = sh('netstat -tulpn 2>/dev/null | grep 127.0.0.1:{:d}'
                .format(SPHINX_AUTOBUILD_PORT), capture=True, ignore_error=True)
    pid = result.strip()
    pid = pid.split()[-1] if pid else None
    pid = pid.split('/', 1)[0] if pid and pid != '-' else None

    return pid


@task
@needs("stopdocs")
def autodocs():
    "create Sphinx docs locally, and start a watchdog"
    build_dir = path('docs/_build')
    index_html = build_dir / 'html/index.html'
    if build_dir.exists():
        build_dir.rmtree()

    with pushd("docs"):
        print "\n*** Generating API doc ***\n"
        sh("sphinx-apidoc -o apidoc -f -T -M ../src/pyrocore")
        print "\n*** Generating HTML doc ***\n"
        sh('nohup %s/Makefile SPHINXBUILD="sphinx-autobuild -p %d'
           ' -i \'.*\' -i \'*.log\' -i \'*.png\' -i \'*.txt\'" html >autobuild.log 2>&1 &'
           % (os.getcwd(), SPHINX_AUTOBUILD_PORT))

    for i in range(25):
        time.sleep(2.5)
        pid = watchdog_pid()
        if pid:
            sh("touch docs/index.rst")
            sh('ps {}'.format(pid))
            url = 'http://localhost:{port:d}/'.format(port=SPHINX_AUTOBUILD_PORT)
            print("\n*** Open '{}' in your browser...".format(url))
            break


@task
def stopdocs():
    "stop Sphinx watchdog"
    for i in range(4):
        pid = watchdog_pid()
        if pid:
            if not i:
                sh('ps {}'.format(pid))
            sh('kill {}'.format(pid))
            time.sleep(.5)
        else:
            break


#
# Testing
#

@task
@needs("nosetests")
def test():
    "run unit tests"


@task
def coverage():
    "generate coverage report and show in browser"
    coverage_index = path("build/coverage/index.html")
    coverage_index.remove()
    sh("paver test")
    coverage_index.exists() and webbrowser.open(coverage_index)


@task
@needs("build")
def functest():
    "functional test of the command line tools"
    bindir = os.path.dirname(sys.executable)
    sh(bindir + "/mktor -o build/pavement.torrent pavement.py http://example.com/")
    sh(bindir + "/mktor -o build/tests.torrent -x '*.pyc' -r 'pyroscope tests' --private src/tests/ http://example.com/")
    sh(bindir + "/lstor build/*.torrent")


@task
def installtest():
    "test of fresh installation"
    testdir = path("build/install-test")
    if testdir.exists():
        testdir.rmtree()

    if os.environ.get('TRAVIS', '').lower() == 'true':
        sh("git clone https://github.com/pyroscope/pyrocore.git " + testdir)
    else:
        sh("git clone . " + testdir)

    testbin = testdir / "test-bin"
    testbin.makedirs()
    os.environ["BIN_DIR"] = testbin.abspath()
    os.environ["PROJECT_ROOT"] = ''
    with pushd(testdir):
        sh("./update-to-head.sh")
        sh("./test-bin/pyroadmin --version")

#
# Release Management
#
@task
@needs(["dist_clean", "minilib", "generate_setup", "sdist"])
def release():
    "check release before upload to PyPI"
    sh("paver bdist_wheel")
    wheels = path("dist").files("*.whl")
    if not wheels:
        error("\n*** ERROR: No release wheel was built!")
        sys.exit(1)
    if any(".dev" in i for i in wheels):
        error("\n*** ERROR: You're still using a 'dev' version!")
        sys.exit(1)

    # Check that source distribution can be built and is complete
    print
    print "~~~ TESTING SOURCE BUILD".ljust(78, '~')
    sh( "{ command cd dist/ && unzip -q %s-%s.zip && command cd %s-%s/"
        "  && /usr/bin/python setup.py sdist >/dev/null"
        "  && if { unzip -ql ../%s-%s.zip; unzip -ql dist/%s-%s.zip; }"
        "        | cut -b26- | sort | uniq -c| egrep -v '^ +2 +' ; then"
        "       echo '^^^ Difference in file lists! ^^^'; false;"
        "    else true; fi; } 2>&1"
        % tuple([project["name"], version] * 4)
    )
    path("dist/%s-%s" % (project["name"], version)).rmtree()
    print "~" * 78

    print
    print "~~~ sdist vs. git ".ljust(78, '~')
    subprocess.call(
        "unzip -v dist/pyrocore-*.zip | egrep '^ .+/' | cut -f2- -d/ | sort >./build/ls-sdist.txt"
        " && git ls-files | sort >./build/ls-git.txt"
        " && $(which colordiff || echo diff) -U0 ./build/ls-sdist.txt ./build/ls-git.txt || true", shell=True)
    print "~" * 78

    print
    print "Created", " ".join([str(i) for i in path("dist").listdir()])
    print "Use 'paver sdist bdist_wheel' to build the release and"
    print "    'twine upload dist/*.{zip,whl}' to upload to PyPI"
    print "Use 'paver dist_docs' to prepare an API documentation upload"


#
# Main
#
setup(**project)
