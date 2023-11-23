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

import string
import logging
from typing import Any, TypeVar, Concatenate
from functools import wraps
from xml.etree import ElementTree
from collections.abc import Callable

import requests
from typing_extensions import Protocol, ParamSpec

__all__ = ['api_client', 'get', 'post', 'put', 'patch', 'delete', 'api_client_method']

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())


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


APIEndpointP = ParamSpec('APIEndpointP')
APIEndpointT = TypeVar('APIEndpointT')

APIEndpointHandler = Callable[APIEndpointP, APIEndpointT]
APIEndpoint = Callable[Concatenate[Any, APIEndpointP], APIEndpointT]


class APIDecoratorFactory(Protocol):
    def __call__(self, endpoint: str, *, version: int = 1, use_api: bool = True,
                 json: bool = True, xml: bool = False, **g_kwargs) -> Callable[
                     ...,
                     Callable[
                         [Callable[APIEndpointP, APIEndpointT]],
                         Callable[Concatenate[Any, APIEndpointP], APIEndpointT]
                     ]]: ...


def api_client_method(method: str) -> APIDecoratorFactory:
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
        def __missing__(self, key: Any) -> str:
            return ''

    def request(endpoint: str, *, version: int = 1, use_api: bool = True,
                json: bool = True, xml: bool = False, **g_kwargs) -> Callable[
                        [Callable[APIEndpointP, APIEndpointT]],
                        Callable[Concatenate[Any, APIEndpointP], APIEndpointT]
                ]:
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
        :param bool json: Toggles JSON parsing of response before returning
        :param dict g_kwargs: Any extra keyword argument will be passed to requests
        """

        def request_decorator(func: Callable[APIEndpointP, APIEndpointT]) -> Callable[
                Concatenate[Any, APIEndpointP], APIEndpointT]:
            """Return wrapped function.

            :param function func: Function to decorate
            """

            @wraps(func)
            def request_wrapper(self, /, *args: APIEndpointP.args,
                                **kwargs: APIEndpointP.kwargs) -> APIEndpointT:
                """Wrap function in REST API call.

                :param list args: Passed to the function being wrapped
                :param dict kwargs: Any kwargs will be passed to requests
                """
                if self._url is None:
                    raise APINoURLError()

                if not hasattr(self, '__client_session'):
                    _logger.info("Creating new requests session")
                    self.__client_session = requests.Session()

                param_endpoint = endpoint.format_map(dict_safe(kwargs))

                # Remove parameters meant for endpoint formatting
                formatter = string.Formatter()
                for x in formatter.parse(endpoint):
                    kwargs.pop(x[1], None)  # type: ignore

                url = self._url.format(version=version)
                endpoint_format = f"{url}{param_endpoint}"

                if not use_api:
                    endpoint_format = param_endpoint
                if endpoint_format[-1] == "/":
                    endpoint_format = endpoint_format[:-1]

                _logger.debug(f"Making request to {endpoint_format}")

                cookies = None
                if hasattr(self, '_cookies'):
                    cookies = self._cookies
                elif hasattr(self, '_session'):
                    _logger.warning("_session is deprecated. Use _cookies instead.")
                    cookies = self._session

                # This line generates some errors due to kwargs being passed to
                # the non-kwarg-ed requests.request method
                response = self.__client_session.request(
                    method, endpoint_format, timeout=self.__api_timeout,
                    cookies=cookies, **kwargs, **g_kwargs)  # type: ignore
                endpoint_response: Any = response

                if json:
                    endpoint_response = response.json()

                    if not endpoint_response:
                        raise APIEmptyResponseError()
                    elif self.__api_status_key in endpoint_response:
                        status_code = endpoint_response[self.__api_status_key]
                        _logger.warning(f"Code {status_code} in {endpoint_format}")

                        if self.__api_status_handler is not None:
                            self.__api_status_handler(status_code)
                        else:
                            raise APIStatusError('Server responded with an error code')

                    if self.__api_results_key in endpoint_response:
                        endpoint_response = endpoint_response[self.__api_results_key]
                elif xml:
                    endpoint_response = ElementTree.fromstring(response.text)

                return func(self, endpoint_response, *args)
            return request_wrapper
        return request_decorator
    return request


APIClient = TypeVar('APIClient', bound=type[Any])
APIStatusHandler = Callable[[Any], None] | None


def api_client(url: str | None = None, /, *, timeout: int | None = None,
               status_handler: APIStatusHandler = None, status_key: str = 'status',
               results_key: str = 'results') -> Callable[[APIClient], APIClient]:
    """Annotate a class to use the api client method decorators

    Basic usage:
        >>> @api_client("https://example.org/api")
        >>> class MyClient:
        ...     ...

    :param string url: The URL of the API root which can include placeholders (see docs)
    :param int timeout: The timeout to use in seconds
    :param Callable status_handler: A function that handles error codes from the API
    :param string status_key: The key of the API response that contains the status code
    :param string results_key: The key of the API response that contains the results
    """

    def wrap(cls: APIClient) -> APIClient:
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
