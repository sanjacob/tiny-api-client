Quick Guide
===========

.. _basics:

Basics
------

To begin, import the class decorator, and any http methods you will use

::

        from tiny_api_client import api_client, get


Then, create a class for your very own API client

::

        @api_client("https://example.org/api")
        class MyAPIClient:
                ...

Finally, declare your endpoints one by one, using one of the valid HTTP methods

::

            @get('/profile/{user_id}/comments/{comment_id}')
            def fetch_comments(self, response):
                return response

That's it, you are done creating your API client

::

        client = MyAPIClient()
        client.fetch_comments(user_id='me') # parameters are optional
        [{'id': '001', 'content': 'This is my first comment'}, ...]

        client.fetch_comments(user_id='me', comment_id='001')
        {'id': '001', 'content': 'This is my first comment'}


In its entirety, the client looks like this, short and sweet

::

        from tiny_api_client import api_client, get

        @api_client("https://example.org/api")
        class MyAPIClient:
            @get('/profile/{user_id}/comments/{comment_id}')
            def fetch_comments(self, response):
                return response


To pass along a request body, do so as you would normally when calling
`requests.post`.

::

        >>> client.create_comment(data={...})
        >>> client.create_comment(json={...})


You can either return the JSON response directly as seen before,
or use custom classes to parse and structure the API responses
(for example, with pydantic)

::

        from pydantic import BaseModel

        class Kitten(BaseModel):
            ...

        @api_client('https://example.org/api')
        class KittenAPIClient:
            @get("/kitten/{kitten_name}")
            def find_kitten(self, response) -> list[Kitten] | Kitten:
                if isinstance(response, list):
                    return [Kitten(**item) for item in response]
                else:
                    return Kitten(**response)


Advanced
--------

- Handle non-JSON data and streams

The library will call `.json()` on the server response for you by default. But you can also turn this off on an endpoint basis


::

        @get("/comments/{comment_id}", json=False)
        def fetch_comment(self, response):
            return response.text()

        >>> client.fetch_comment(comment_id=...)
        A plaintext HTTP response


- Parse XML response

If one of your endpoints is still using XML you can let the library parse
the response for you with `xml.etree.ElementTree`. Note that as with JSON
parsing, you must handle any errors produced from this.

::

        @get("/xml/comments/{comment_id}", json=False, xml=True)
        def fetch_xml_comment(self, response):
            return response


- Custom *requests* parameters

Any keyword parameters included in either the endpoint declaration or the call to it will be passed to requests when called.

::

        @get("/file/{file_hash}", json=False, stream=True) # in endpoint declaration
        def download_file(self, response):
            for chunk in r.iter_content(chunk_size=1024):
                # Handle file content


        >>> client.download_file(file_hash='...', auth=..., headers=...) # passed at runtime

For the full list of accepted parameters, see the `requests`_ documentation.

.. _requests: https://requests.readthedocs.io/en/latest/api/#requests.request


- Dynamic API URL

Don't know the URL at import time? No problem, define a `_url` member at runtime instead.

.. note::

        Please do not use a `@property` for this

::

        @api_client()
        class ContinentAPIClient:
        def __init__(api_url: str):
            self._url = api_url

            @get("/countries")
            def fetch_countries(self, response):
                return response


>>> africa = ContinentAPIClient("https://africa.example.org/api")
>>> europe = ContinentAPIClient("https://europe.example.org/api")

This technique is useful in situations where there is a common API with different
instances hosted independently, and you don't know beforehand which instance you
are connecting to.


- Pass arguments to the endpoint handler

Any positional parameters will be passed to the response handler, which can
aid in post-request validation or parsing, if desired.

::

        @get('/photos/{photo_id}')
        def fetch_photo(self, response, expected_format):
            if response['format'] != expected_format:
                raise ValueError()

        >>> client.fetch_photo('jpeg', photo_id='PHOTO_001')


- Unpack results from response dict

If the server responds with the result inside a dictionary, you can directly retrieve the result instead

::

        @get("/quotes/{quote_id}", results_key='results')
        def fetch_quotes(self, response) -> list[str]:
            return response

        >>> client.fetch_quote(quote_id=...) # Server response: {'results': ['An apple a day...', ...]}
        ['An apple a day...', ...]


- Include an optional `{version}` placeholder on an endpoint basis

::

        @api_client('https://example.org/api/public/v{version}')
        class MyAPIClient:
            @get('/users/{user_id}', version=3): # will call https://example.org/api/public/v3/users/{user_id}
            ...


Error Handling
--------------

Exceptions
^^^^^^^^^^

The library can throw `APIEmptyResponseError` and `APIStatusError`, both of which
are subclassed from `APIClientError`.
Independent of this, it will not catch any error thrown by requests or the conversion
of the response to JSON, so you will need to decide on a strategy to handle such errors.

::

        from tiny_api_client import APIEmptyResponseError, APIStatusError
        from requests import RequestException
        from json import JSONDecodeError

        try:
            client.fetch_users()
        except APIEmptyResponseError:
            print("The API returned an empty string")
        except APIStatusError:
            print("The JSON response contained a status code")
        except RequestException:
            print("The request could not be completed")
        except JSONDecodeError:
            print("The server response could not be parsed into JSON")

Status Codes
^^^^^^^^^^^^

If your API can return an error code in the JSON response itself, the library
can make use of this. You can either declare an error handler, or let the library
throw an `APIStatusError`.

::

        @api_client('https://example.org', status_key='status',
                    status_handler=lambda x: raise MyCustomError(x))
        class MyClient:
        ...

        >>> client = MyClient()
        >>> client.fetch_profile() # Server response: {'status': '404'}
        Traceback (most recent call last):
            File "<stdin>", line 1, in <module>
        MyCustomError(404)


Session/Cookies
---------------

- Define a `_cookies` property and all requests will include this cookie jar

::

        from http.cookiejar import CookieJar

        @api_client('https://example.org')
        class MyAPIClient:
            def __init__(self, cookies: CookieJar | dict):
                self._cookies = cookies


.. note::

        Please do not use a `@property` for this


.. deprecated:: 1.1.0

        self._session (which served the same purpose) is deprecated

- Make a request to a different server

There might come a time when you wish to make a request to a different server within the same session, without implementing your own logic

::

        @get("{external_url}", use_api=False)
        def fetch_external_resource(self, response):
            return response

        >>> client.fetch_external_resource(external_url="https://example.org/api/...")


Reserved Names
--------------

The following are meant to be set by the developer if needed

- `self._cookies`
- `self._url`

.. deprecated:: 1.1.0

        self._session


Tiny API Client reserves the use of the following member names, where * is a wildcard.

- `self.__client_*`: For client instance attributes
- `self.__api_*`: For class wide client attributes
