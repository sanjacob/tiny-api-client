.. Tiny API Client documentation master file, created by
   sphinx-quickstart on Mon Nov 20 16:04:27 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

🐝 Tiny API Client
==================

The short and sweet way to create an API client
-----------------------------------------------


::

        from tiny_api_client import api_client, get

        @api_client("https://example.org/api/v{version}", timeout=10)
        class MyClient:
            @get("/posts/{post_id}", version=2)
            def get_posts(self, response):
                return response

        >>> client = MyClient()
        >>> client.get_posts() # route parameters are optional


Tiny API Client is a wrapper for `requests` that enables you to succintly write API clients
without much effort. Calls on each instance of a client class will share a `requests.Session`
with cookie preservation and improved performance due to request pooling.

To get started, see the :ref:`basics` first.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quick
   api_reference



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
