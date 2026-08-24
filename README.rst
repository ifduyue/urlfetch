urlfetch |github-actions-badge| |furyio-badge|
==========================================================

.. |github-actions-badge| image:: https://github.com/ifduyue/urlfetch/actions/workflows/test.yml/badge.svg
    :target: https://github.com/ifduyue/urlfetch/actions/workflows/test.yml

.. |furyio-badge| image:: https://badge.fury.io/gh/ifduyue%2Furlfetch.svg
    :target: https://badge.fury.io/gh/ifduyue%2Furlfetch

urlfetch is a simple, lightweight and easy to use HTTP client for Python.
It is distributed as a single file module and has no depencencies other than the Python Standard Library.


Highlights
-------------

* Distributed as a single file module, has no depencencies other than the Python Standard Library.
* Pure Python, works fine with gevent_.
* Small codebase, about 1000 lines and 30% are comments and blank lines. Only 10 minutes you can know every detail.
* Random user-agent.
* Support streaming.

.. _gevent: http://www.gevent.org/

Installation
-------------
::

    $ pip install urlfetch


Hello, world
-------------

.. code-block:: python

    import urlfetch

    response = urlfetch.get('http://python.org/')
    print(response.status, response.reason)
    print(len(response.content))

Uploading files
----------------

.. code-block:: python

    import urlfetch

    response = urlfetch.post(
        'http://127.0.0.1:8888/upload',
        headers = {
            'Referer': 'http://127.0.0.1/',
        },
        files = {
            'fieldname1': open('/path/to/file', 'rb'),
            #'fieldname2': 'file content', # file must have a filename
            'fieldname3': ('filename', open('/path/to/file2', 'rb')),
            'fieldname4': ('filename', 'file content'),
        },
        data = {
            'foo': 'bar'
        },
    )

    print(response.status, response.content)


Testing
--------

.. __: http://bottlepy.org/
.. __: http://gunicorn.org/

To run the tests, urlfetch relies on `bottle`__ and `gunicorn`__.
Install them and run::

    $ python tests/testall.py


Releasing
---------

Pushing a version tag publishes the package to PyPI with `Trusted Publishing`_
and creates a GitHub Release. The tag must match ``urlfetch.__version__``
(for example ``v2.0.1``).

::

    git tag vX.Y.Z
    git push origin vX.Y.Z

Release notes come from the matching section in ``doc/changelog.rst``, followed
by GitHub's auto-generated notes. sdist and wheel are attached to the release.

One-time PyPI setup (project owner)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On https://pypi.org/manage/project/urlfetch/settings/publishing/ add a GitHub
Trusted Publisher:

* Owner: ``ifduyue``
* Repository: ``urlfetch``
* Workflow: ``publish.yml``
* Environment: ``pypi``

The GitHub environment ``pypi`` is restricted to tags matching ``v*``. No PyPI
API token is stored in the repository.

.. _Trusted Publishing: https://docs.pypi.org/trusted-publishers/

