.. Include text from the place where GitHub sees it.
.. include:: ../CONTRIBUTING.rst

Performing a Release
--------------------

#. Check for and fix ``pylint`` violations::

    paver lint -m

#. Verify ``debian/changelog`` for completeness and the correct version, and bump the release date::

    dch -r

#. Check Travis CI status at https://travis-ci.org/pyroscope/pyrocore

#. Remove ‘dev’ version tagging from ``setup.cfg``, and perform a release check::

    sed -i -re 's/^(tag_[a-z ]+=)/##\1/' setup.cfg
    paver release

#. Commit and tag the release::

    git status  # check all is committed
    tag="v$(dpkg-parsechangelog | grep '^Version:' | awk '{print $2}')"
    git tag -a "$tag" -m "Release $tag"

#. Build the final release and upload it to PyPI::

    paver dist_clean sdist bdist_wheel
    twine upload dist/*.{zip,whl}
