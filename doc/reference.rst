Reference
==============

.. module:: urlfetch
   :platform: Unix, Windows
   :synopsis: HTTP Client
.. moduleauthor:: Yue Du <ifduyue@gmail.com>

.. autoclass:: Response
    :members:
    :undoc-members:
    :private-members:

.. autoclass:: Session
    :members:
    :undoc-members:
    :private-members:


.. autofunction:: request
.. autofunction:: fetch

.. autofunction:: get
.. autofunction:: post
.. autofunction:: head
.. autofunction:: put
.. autofunction:: delete
.. autofunction:: options
.. autofunction:: trace
.. autofunction:: patch

Exceptions
~~~~~~~~~~~

.. autoclass:: UrlfetchException
.. autoclass:: ContentLimitExceeded
.. autoclass:: URLError
.. autoclass:: ContentDecodingError
.. autoclass:: TooManyRedirects
.. autoclass:: Timeout

helpers
~~~~~~~~~~~

.. autofunction:: parse_url
.. autofunction:: get_proxies_from_environ
.. autofunction:: mb_code
.. autofunction:: random_useragent
.. autofunction:: url_concat
.. autofunction:: choose_boundary
.. autofunction:: encode_multipart
