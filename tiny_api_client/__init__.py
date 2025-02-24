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

# Copyright (C) 2024, Jacob Sánchez Pérez

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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301  USA

import logging
import requests
import string
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from requests.adapters import HTTPAdapter
from typing import Any, Concatenate, ParamSpec, Protocol, TypeVar
from urllib3.util.retry import Retry
from xml.etree import ElementTree

__all__ = ['api_client', 'get', 'post', 'put', 'patch', 'delete']

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())

# Typing

P = ParamSpec('P')
T = TypeVar('T')

APIStatusHandler = Callable[[Any, Any, Any], None] | None
_StatusHandler = Callable[[Any, Any], None] | None

APIClient = TypeVar('APIClient', bound=type[Any])


class RequestDecorator(Protocol):
    def __call__(
        self, func: Callable[Concatenate[Any, Any, P], T]
    ) -> Callable[Concatenate[Any, P], T]: ...


class DecoratorFactory(Protocol):
    def __call__(
        self, route: str, *, version: int = 1, use_api: bool = True,
        json: bool = True, xml: bool = False, **g_kwargs: Any
    ) -> RequestDecorator: ...


# Exceptions

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


# Tiny API Client

@dataclass
class Endpoint:
    route: str
    version: int
    use_api: bool
    json: bool
    xml: bool
    kwargs: dict[str, Any]


def _format_endpoint(url: str, endpoint: str, use_api: bool,
                     positional_args: dict[str, Any]) -> str:
    """Build final endpoint URL for an API call."""
    param_map = defaultdict(lambda: '', positional_args)
    route_params = endpoint.format_map(param_map)
    endpoint_url = f"{url}{route_params}" if use_api else route_params
    return endpoint_url.rstrip('/')


def _pop_api_kwargs(endpoint: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Remove positional endpoint arguments from kwargs before passing
    additional arguments to `requests`.
    """
    formatter = string.Formatter()
    for x in formatter.parse(endpoint):
        if x[1] is not None:
            kwargs.pop(x[1], None)
    return kwargs


def _make_request(client: Any, method: str, endpoint: str,
                  **kwargs: Any) -> Any:
    """Use `requests` to send out a request to the API endpoint."""
    if not hasattr(client, '__client_session'):
        # Create a session to reuse connections
        _logger.info("Creating new requests session")
        client.__client_session = requests.Session()
        # Set custom adapter for retries
        adapter = HTTPAdapter(max_retries=client.__api_max_retries)
        client.__client_session.mount("http://", adapter)
        client.__client_session.mount("https://", adapter)

    # The following assertion causes issues in testing
    # since MagicMock is not an instance of Session
    # Thus, the return type has to be Any for now
    # assert isinstance(client.__client_session, requests.Session)

    _logger.debug(f"Making request to {endpoint}")

    cookies = None
    if hasattr(client, '_cookies'):
        cookies = client._cookies
    elif hasattr(client, '_session'):
        _logger.warning("_session is deprecated.")
        cookies = client._session

    return client.__client_session.request(
        method, endpoint,
        timeout=client.__api_timeout,
        cookies=cookies, **kwargs
    )


def _handle_response(response: Any,
                     json: bool, xml: bool,
                     status_key: str, results_key: str,
                     status_handler: _StatusHandler) -> Any:
    """Parse json or XML response after request is complete"""
    endpoint_response: Any = response

    if json:
        endpoint_response = response.json()

        if not endpoint_response:
            raise APIEmptyResponseError()

        if status_key in endpoint_response:
            status_code = endpoint_response[status_key]
            _logger.warning(f"Code {status_code} from {response.url}")

            if status_handler is not None:
                status_handler(status_code, endpoint_response)
            else:
                raise APIStatusError('Server responded with an error code')

        if results_key in endpoint_response:
            endpoint_response = endpoint_response[results_key]
    elif xml:
        endpoint_response = ElementTree.fromstring(response.text)

    return endpoint_response


def make_api_call(method: str, client: Any,
                  endpoint: Endpoint, **kwargs: Any) -> Any:
    """Calls the API endpoint and handles result."""
    if client._url is None:
        raise APINoURLError()

    # Build final API endpoint URL
    url = client._url.format(version=endpoint.version)
    route = _format_endpoint(url, endpoint.route, endpoint.use_api, kwargs)

    # Remove parameters meant for endpoint formatting
    kwargs = _pop_api_kwargs(endpoint.route, kwargs)

    response = _make_request(client, method, route,
                             **kwargs, **endpoint.kwargs)
    endpoint_response = _handle_response(
        response,
        endpoint.json,
        endpoint.xml,
        client.__api_status_key,
        client.__api_results_key,
        client.__api_status_handler)

    return endpoint_response


def api_client_method(method: str) -> DecoratorFactory:
    """Create a decorator factory for one of the http methods

    This superfactory can create factories for arbitrary http verbs
    (GET, POST, etc.). Unless specifying an http verb not already
    covered by this library, this function should not be called
    directly.

    Basic usage:
        >>> get = api_client_method('GET')
        >>> @get("/profile/{user_id}")
        ... def fetch_profile(response):
        ...    return response
        >>> client.fetch_profile(user_id=...)

    :param str method: The HTTP verb for the decorator
    """

    def request(route: str, *, version: int = 1, use_api: bool = True,
                json: bool = True, xml: bool = False,
                **request_kwargs: Any) -> RequestDecorator:
        """Declare an endpoint with the given HTTP method and parameters

        Basic usage:
            >>> from tiny_api_client import get, post
            >>> @get("/posts")
            ... def get_posts(self, response):
            ...     return response
            >>> @post("/posts")
            ... def create_post(self, response):
            ...     return response

        :param str endpoint: Endpoint including positional placeholders
        :param int version: Replaces version placeholder in API URL
        :param bool json: Toggle JSON parsing of response
        :param bool xml: Toggle XML parsing of response
        :param dict request_kwargs: Any keyword arguments passed to requests
        """
        endpoint = Endpoint(route, version, use_api, json, xml, request_kwargs)

        def request_decorator(func: Callable[Concatenate[Any, Any, P], T]
                              ) -> Callable[Concatenate[Any, P], T]:
            """Decorator created when calling @get(...) and others.

            :param function func: Function to decorate
            """

            @wraps(func)
            def request_wrapper(self: Any, /,
                                *args: P.args, **kwargs: P.kwargs) -> T:
                """Replace endpoint parameters and call API endpoint,
                then execute user-defined API endpoint handler.

                :param list args: Passed to the function being wrapped
                :param dict kwargs: Any kwargs are passed to requests
                """
                response = make_api_call(method, self, endpoint, **kwargs)
                return func(self, response, *args)
            return request_wrapper
        return request_decorator
    return request


def api_client(url: str | None = None, /, *,
               max_retries: int | Retry = 0,
               timeout: int | None = None,
               status_handler: APIStatusHandler = None,
               status_key: str = 'status',
               results_key: str = 'results'
               ) -> Callable[[APIClient], APIClient]:
    """Annotate a class to use the api client method decorators

    Basic usage:
        >>> @api_client("https://example.org/api")
        >>> class MyClient:
        ...     ...

    :param str url: The root URL of the API server
    :param int max_retries: Max number of retries for network errors
    :param int timeout: Timeout for requests in seconds
    :param Callable status_handler: Error handler for status codes
    :param str status_key: Key of response that contains status codes
    :param str results_key: Key of response that contains results
    """

    def wrap(cls: APIClient) -> APIClient:
        cls._url = url
        cls.__api_max_retries = max_retries
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
