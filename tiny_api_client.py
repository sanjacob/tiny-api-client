"""
Tiny API Client

The short and sweet way to create an API client

Basic usage:
    >>> from tiny_api_client import api_client, get
    >>> @api_client("https://example.org/api")
    ... class MyClient:
    ...     @get("/profile/{user_id}")
    ...     def fetch_profile(response):
    ...        return response
    >>> client = MyClient()
    >>> client.fetch_profile(user_id=...)

"""

# Copyright (C) 2023, Jacob Sánchez Pérez
 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import abc
import string
import logging
import requests
from functools import wraps
from xml.etree import ElementTree
from dataclasses import _set_new_attribute

from collections.abc import Callable

__all__ = ['api_client', 'get', 'post', 'put', 'patch', 'delete', 'api_client_method']

_logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """Base error class for the API Client"""
    pass


class APIEmptyResponseError(APIClientError):
    """The API response is empty"""
    pass


class APIStatusError(APIClientError):
    """The API returned an error status"""
    pass


class APINoURLError(APIClientError):
    """The API has no URL declared"""
    pass


def api_client_method(method: str):
    """Construct an API client decorator function for an specific HTTP method

    Basic usage:
        >>> get = api_client_decorator('GET')
        >>> @get("/profile/{user_id}")
        ... def fetch_profile(response):
        ...    return response
        >>> client.fetch_profile(user_id=...)

    :param string method: The HTTP verb for the decorator
    """

    class dict_safe(dict):
        def __missing__(self, key):
            return ''

    def request(endpoint: str, *, version: int = 1, use_api: bool = True,
                json: bool = True, xml: bool = False, **g_kwargs) -> Callable[[Callable], Callable]:
        """Declare an endpoint with a given HTTP method

        Basic usage:
            >>> from tiny_api_client import get, post
            >>> @get("/posts")
            ... def get_posts(self, response):
            ...     return response
            >>> @post("/posts")
            ... def create_post(self, response):
            ...     return response

        :param string endpoint: Endpoint to make call to, including placeholders
        :param int version: API version to which the endpoint belongs
        :param bool json: If false, returns raw requests response, otherwise returns JSON Object
        :param dict g_kwargs: Any extra keyword argument will be passed to requests
        """

        def request_decorator(func: Callable) -> Callable:
            """Return wrapped function.

            :param function func: Function to decorate
            """

            @wraps(func)
            def request_wrapper(self, *args, **kwargs):
                """Wrap function in REST API call.

                :param list args: Passed to the function being wrapped
                :param dict kwargs: Any kwargs will be passed to requests
                """
                param_endpoint = endpoint.format_map(dict_safe(kwargs))

                # Remove parameters meant for endpoint formatting
                formatter = string.Formatter()
                for x in formatter.parse(endpoint):
                    kwargs.pop(x[1], None)

                if self._url is None:
                    raise APINoURLError()

                url = self._url.format(version=version)

                endpoint_format = f"{url}{param_endpoint}"

                if not use_api:
                    endpoint_format = param_endpoint
                if endpoint_format[-1] == "/":
                    endpoint_format = endpoint_format[:-1]

                _logger.debug(f"Making request to {endpoint_format}")

                cookies = None
                if hasattr(self, '_session'):
                    cookies = self._session

                response = requests.request(method, endpoint_format, timeout=self.__api_timeout,
                                            cookies=cookies, **kwargs, **g_kwargs)
                if json:
                    response = response.json()

                    if not response:
                        raise APIEmptyResponseError()
                    elif self.__api_status_key in response:
                        _logger.warn(f"Code {response[self.__api_status_key]} on request to {endpoint_format}")

                        if self.__api_status_handler is not None:
                            self.__api_status_handler(response[self.__api_status_key])
                        else:
                            raise APIStatusError('Server responded with an error code')

                    if self.__api_results_key in response:
                        response = response[self.__api_results_key] 
                elif xml:
                    response = ElementTree.fromstring(response.content)

                return func(self, response, *args)
            return request_wrapper
        return request_decorator
    return request


def api_client(url: str | None = None, /, *, timeout: int = None, status_handler: Callable = None,
               status_key: str = 'status', results_key: str = 'results'):
    """Annotate a class to use the api client method decorators

    Basic usage:
        >>> @api_client("https://example.org/api")
        >>> class MyClient:
        ...     ...
    
    :param string url: The URL of the API root which can include placeholders (see docs) 
    :param int timeout: The timeout to use in seconds
    :param Callable status_handler: A function that handles error codes from the API
    :param string status_key: The key of the API response that contains the status code
    :param string results_key: The key of the API response that contains a list of results
    """

    def wrap(cls):
        cls._url = url
        cls.__api_timeout = timeout
        cls.__api_status_handler = status_handler
        cls.__api_status_key = status_key
        cls.__api_results_key = results_key
        return cls

    return wrap


get = api_client_method('GET')
post = api_client_method('POST')
put = api_client_method('PUT')
patch = api_client_method('PATCH')
delete = api_client_method('DELETE')
