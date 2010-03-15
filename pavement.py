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

import os

from paver.easy import *
from paver.setuputils import setup

from setuptools import find_packages


#
# Project Metadata
#

changelog = path("debian/changelog")
if not changelog.exists():
    changelog = path("../debian/changelog")

name, version = open(changelog).readline().split(" (", 1)
version, _ = version.split(")", 1)

project = dict(
    # egg
    name = "pyrocore",
    version = version,
    package_dir = {"": "src"},
    packages = find_packages("src", exclude = ["tests"]),
    entry_points = {
        "console_scripts": [
            "mktor = pyrocore.scripts.mktor:run",
            "lstor = pyrocore.scripts.lstor:run",
            "chtor = pyrocore.scripts.chtor:run",
            "pyroadmin = pyrocore.scripts.pyroadmin:run",
            "rtcontrol = pyrocore.scripts.rtcontrol:run",
            "rtmv = pyrocore.scripts.rtmv:run",
        ],
    },
    include_package_data = True,
    zip_safe = True,
    data_files = [
        ("EGG-INFO", [
            "README", "LICENSE", "debian/changelog", 
        ]),
    ],

    # dependencies
    install_requires = [
    ],
    setup_requires = [
    ],

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
    keywords = "bittorent rtorrent cli python",
    classifiers = [
        # see http://pypi.python.org/pypi?:action=list_classifiers
        #"Development Status :: 3 - Alpha",
        "Development Status :: 4 - Beta",
        #"Development Status :: 5 - Production/Stable",
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
def docs():
    """ Create documentation.
    """
    print "No core docs yet!"


#
# Testing
#

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


#
# Main
#
setup(**project)

