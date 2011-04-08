# -*- coding: utf-8 -*-
""" PyroCore - Python Torrent Tools Core Package.

    PyroScope is a collection of tools for the BitTorrent protocol and especially the rTorrent client.

    This is the core package and basic command line tools subproject.

    Copyright (c) 2010 The PyroScope Project <pyroscope.project@gmail.com>

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
import webbrowser

from paver.easy import *
from paver.setuputils import setup

try:
    from pyrobase.paver.easy import *
except ImportError:
    pass # dependencies not yet installed

from setuptools import find_packages


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
        ],
    },
    include_package_data = True,
    zip_safe = False,
    data_files = [
        ("EGG-INFO", [
            "README", "LICENSE", "debian/changelog", 
        ]),
    ],

    # dependencies
    setup_requires = [
    ],
    install_requires = [
        "pyrobase>=0.1dev",
    ],
    extras_require = {
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
    url = "http://code.google.com/p/pyroscope/",
    keywords = "bittorrent rtorrent cli python",
    classifiers = [
        # see http://pypi.python.org/pypi?:action=list_classifiers
        #"Development Status :: 3 - Alpha",
        #"Development Status :: 4 - Beta",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.5",
        "Topic :: Communications :: File Sharing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)

options(
    setup=project,
    docs=Bunch(docs_dir="docs/apidocs"),
)

setup(**project)


#
# Build
#
@task
@needs(["setuptools.command.egg_info"])
def bootstrap():
    """ Initialize project.
    """
    # Link files shared by subprojects
    debian = path("debian")
    debian.exists() or debian.makedirs()
    
    for shared in ("debian/changelog", "LICENSE"):
        path(shared).exists() or (path("..") / shared).link(shared)


@task
@needs("docs")
def dist_docs():
    """ Create a documentation bundle.
    """
    dist_dir = path("dist")
    docs_package = path("%s/%s-%s-docs.zip" % (dist_dir.abspath(), options.setup.name, options.setup.version))

    dist_dir.exists() or dist_dir.makedirs()
    docs_package.exists() and docs_package.remove()

    sh(r'cd docs && find . -type f \! \( -path "*/.svn*" -o -name "*~" \) | sort'
       ' | zip -qr -@ %s' % (docs_package,))

    print
    print "Upload @ http://pypi.python.org/pypi?:action=pkg_edit&name=%s" % ( options.setup.name,)
    print docs_package


#
# Testing
#

@task
@needs("nosetests")
def test():
    """ Run unit tests.
    """


@task
def coverage():
    """ Generate coverage report and show in browser.
    """
    coverage_index = path("build/coverage/index.html")
    coverage_index.remove()
    sh("paver test")
    coverage_index.exists() and webbrowser.open(coverage_index)


@task
@needs("setuptools.command.build")
def functest():
    """ Functional test of the command line tools.
    """
    sh("bin/mktor -o build/pavement.torrent pavement.py http://example.com/")
    sh("bin/mktor -o build/tests.torrent -x '*.pyc' -r 'pyroscope tests' --private src/tests/ http://example.com/")
    sh("bin/lstor build/*.torrent")


#
# Release Management
#
@task
@needs("clean")
def dist_clean():
    """ Clean up including dist directory.
    """
    path("dist").rmtree()


@task
@needs(["dist_clean", "minilib", "generate_setup", "sdist"])
def release():
    """ Check release before upload to PyPI.
    """
    sh("paver bdist_egg")

    # Check that source distribution can be built and is complete
    print
    print "~" * 78
    print "TESTING SOURCE BUILD"
    sh(
        "{ cd dist/ && unzip -q %s-%s.zip && cd %s-%s/"
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
    print "Created", " ".join([str(i) for i in path("dist").listdir()])
    print "Use 'paver sdist bdist_egg upload' to upload to PyPI"
    print "Use 'paver dist_docs' to prepare an API documentation upload"

