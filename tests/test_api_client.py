"""Test the tiny_api_client module"""

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

import pytest

from tiny_api_client import api_client, get, post, put, patch, delete
from tiny_api_client import APIEmptyResponseError, APIStatusError


@pytest.fixture
def example_url():
    return 'https://example.org/api/public'


@pytest.fixture
def example_timeout():
    return 1977


@pytest.fixture
def example_note():
    return {'title': 'My Note',
            'content': 'The beat goes round and round',
            'custom_error': '200'}


@pytest.fixture
def mock_requests(mocker, example_note):
    mocked_requests = mocker.patch('tiny_api_client.requests')

    mock_response = mocker.Mock()
    mock_response.json.return_value = example_note

    mocked_requests.Session().request.return_value = mock_response
    return mocked_requests


def get_request_fn(mock_requests):
    return mock_requests.Session().request


def test_get(mock_requests, example_url, example_note):
    @api_client(example_url)
    class MyClient:
        @get('/my-endpoint')
        def get_my_endpoint(self, response):
            return response

    client = MyClient()
    r = client.get_my_endpoint()
    get_request_fn(mock_requests).assert_called_with(
        'GET', f'{example_url}/my-endpoint', timeout=None, cookies=None
    )
    assert r == example_note


def test_post(mock_requests, example_url, example_note):
    @api_client(example_url)
    class MyClient:
        @post('/my-endpoint')
        def post_my_endpoint(self, response):
            return response

    client = MyClient()
    r = client.post_my_endpoint()
    get_request_fn(mock_requests).assert_called_with(
        'POST', f'{example_url}/my-endpoint', timeout=None, cookies=None
    )
    assert r == example_note


def test_put(mock_requests, example_url, example_note):
    @api_client(example_url)
    class MyClient:
        @put('/my-endpoint')
        def put_my_endpoint(self, response):
            return response

    client = MyClient()
    r = client.put_my_endpoint()
    get_request_fn(mock_requests).assert_called_with(
        'PUT', f'{example_url}/my-endpoint', timeout=None, cookies=None
    )
    assert r == example_note


def test_patch(mock_requests, example_url, example_note):
    @api_client(example_url)
    class MyClient:
        @patch('/my-endpoint')
        def patch_my_endpoint(self, response):
            return response

    client = MyClient()
    r = client.patch_my_endpoint()
    get_request_fn(mock_requests).assert_called_with(
        'PATCH', f'{example_url}/my-endpoint', timeout=None, cookies=None
    )
    assert r == example_note


def test_delete(mock_requests, example_url, example_note):
    @api_client(example_url)
    class MyClient:
        @delete('/my-endpoint')
        def delete_my_endpoint(self, response):
            return response

    client = MyClient()
    r = client.delete_my_endpoint()
    get_request_fn(mock_requests).assert_called_with(
        'DELETE', f'{example_url}/my-endpoint', timeout=None, cookies=None
    )
    assert r == example_note


def test_non_json(mocker, example_url):
    mock_requests = mocker.patch('tiny_api_client.requests')
    get_request_fn(mock_requests).return_value = 'This is a plaintext message'

    @api_client(example_url)
    class MyClient:
        @get('/my-endpoint', json=False)
        def get_my_endpoint(self, response):
            return response

    client = MyClient()
    r = client.get_my_endpoint()
    assert r == 'This is a plaintext message'


def test_non_json_xml(mocker, example_url):
    mock_requests = mocker.patch('tiny_api_client.requests')
    mock_response = mocker.Mock()
    mock_response.text = """
    <song>
        <title>First</title>
    </song>
    """

    get_request_fn(mock_requests).return_value = mock_response

    @api_client(example_url)
    class MyClient:
        @get('/my-endpoint', json=False, xml=True)
        def get_my_endpoint(self, response):
            return response

    client = MyClient()
    root = client.get_my_endpoint()
    song = root.find('title')
    assert song.text == 'First'


def test_optional_parameter(mock_requests, example_url):
    @api_client(example_url)
    class MyClient:
        @get('/my-endpoint/{optional_id}')
        def get_my_endpoint(self, response):
            return response

    client = MyClient()
    client.get_my_endpoint()
    get_request_fn(mock_requests).assert_called_with(
        'GET', f'{example_url}/my-endpoint', timeout=None, cookies=None
    )

    client.get_my_endpoint(optional_id='MY_OPTIONAL_ID')
    get_request_fn(mock_requests).assert_called_with(
        'GET', f'{example_url}/my-endpoint/MY_OPTIONAL_ID', timeout=None, cookies=None
    )


def test_multiple_route_parameters(mock_requests, example_url):
    @api_client(example_url)
    class MyClient:
        @get('/my-endpoint/{first_id}/child/{second_id}/child/{third_id}')
        def get_my_endpoint(self, response):
            return response

    client = MyClient()
    client.get_my_endpoint(first_id='1', second_id='22', third_id='333')
    get_request_fn(mock_requests).assert_called_with(
        'GET', f'{example_url}/my-endpoint/1/child/22/child/333',
        timeout=None, cookies=None
    )


def test_positional_endpoint_parameters(mock_requests, example_url):
    @api_client(example_url)
    class MyClient:
        @get('/my-endpoint')
        def get_my_endpoint(self, response, cheese):
            self.cheese = cheese
            return response

    client = MyClient()
    client.get_my_endpoint('my cheese')
    assert client.cheese == 'my cheese'


def test_extra_requests_parameter(mock_requests, example_url):
    @api_client(example_url)
    class MyClient:
        @get('/my-endpoint')
        def get_my_endpoint(self, response):
            return response

    client = MyClient()
    client.get_my_endpoint(my_extra_param='hello world')
    get_request_fn(mock_requests).assert_called_with(
        'GET', f'{example_url}/my-endpoint', timeout=None, cookies=None,
        my_extra_param='hello world'
    )


def test_extra_requests_parameter_endpoint_declaration(mock_requests, example_url):
    @api_client(example_url)
    class MyClient:
        @get('/my-endpoint', my_extra_param='hello world')
        def get_my_endpoint(self, response):
            return response

    client = MyClient()
    client.get_my_endpoint()
    get_request_fn(mock_requests).assert_called_with(
        'GET', f'{example_url}/my-endpoint', timeout=None, cookies=None,
        my_extra_param='hello world'
    )


def test_unpacking(mock_requests, example_url, example_note):
    @api_client(example_url, results_key='content')
    class MyClient:
        @get('/my-endpoint')
        def get_my_endpoint(self, response):
            return response

    client = MyClient()
    r = client.get_my_endpoint()
    get_request_fn(mock_requests).assert_called_with(
        'GET', f'{example_url}/my-endpoint', timeout=None, cookies=None
    )
    assert r == example_note['content']


def test_empty_response_error(mocker, example_url):
    mock_requests = mocker.patch('tiny_api_client.requests')
    mock_response = mocker.Mock()
    mock_response.json.return_value = ""

    get_request_fn(mock_requests).return_value = mock_response

    @api_client(example_url)
    class MyClient:
        @get('/my-endpoint')
        def get_my_endpoint(self, response):
            return response

    client = MyClient()
    with pytest.raises(APIEmptyResponseError):
        client.get_my_endpoint()


def test_endpoint_versions(mock_requests, example_url, example_note):
    @api_client(f"{example_url}/v{{version}}")
    class MyClient:
        @put('/my-endpoint')
        def put_my_endpoint(self, response):
            return response

        @get('/my-endpoint', version=3)
        def get_my_endpoint(self, response):
            return response

        @post('/my-endpoint', version=2)
        def post_my_endpoint(self, response):
            return response

    client = MyClient()
    client.get_my_endpoint()
    get_request_fn(mock_requests).assert_called_with(
        'GET', f'{example_url}/v3/my-endpoint', timeout=None, cookies=None
    )
    client.post_my_endpoint()
    get_request_fn(mock_requests).assert_called_with(
        'POST', f'{example_url}/v2/my-endpoint', timeout=None, cookies=None
    )
    client.put_my_endpoint()
    get_request_fn(mock_requests).assert_called_with(
        'PUT', f'{example_url}/v1/my-endpoint', timeout=None, cookies=None
    )


def test_class_decorator_parameter_timeout(mock_requests, example_url, example_timeout):
    @api_client(example_url, timeout=example_timeout)
    class MyClient:
        @get('/my-endpoint')
        def get_my_endpoint(self, response):
            return response

    client = MyClient()
    client.get_my_endpoint()
    get_request_fn(mock_requests).assert_called_with(
        'GET', f'{example_url}/my-endpoint', timeout=example_timeout, cookies=None
    )


def test_class_decorator_parameter_status_no_handler(mock_requests, example_url):
    @api_client(example_url, status_key='custom_error')
    class MyClient:
        @get('/my-endpoint')
        def get_my_endpoint(self, response):
            return response

    client = MyClient()
    with pytest.raises(APIStatusError) as e:
        client.get_my_endpoint()
        assert str(e.value) == '200'


def test_class_decorator_parameter_status_handler_throws(mock_requests, example_url):
    @staticmethod
    def throw_custom(error_code):
        raise ValueError(error_code)

    @api_client(example_url, status_key='custom_error',
                status_handler=throw_custom)
    class MyClient:
        @get('/my-endpoint')
        def get_my_endpoint(self, response):
            return response

    client = MyClient()
    with pytest.raises(ValueError) as e:
        client.get_my_endpoint()
        assert str(e.value) == '200'


def test_deferred_url_parameter(mock_requests, example_url, example_note):
    @api_client()
    class MyClient:
        def __init__(self, url: str):
            self._url = url

        @get('/my-endpoint')
        def fetch_my_endpoint(self, response):
            return response

    client = MyClient(example_url)
    r = client.fetch_my_endpoint()

    assert r == example_note
    get_request_fn(mock_requests).assert_called_once_with(
        'GET', f'{example_url}/my-endpoint', timeout=None, cookies=None
    )


def test_session_member(mock_requests, example_url, example_note):
    @api_client(example_url)
    class MyClient:
        def __init__(self, session: str):
            self._session = session

        @get('/my-endpoint')
        def fetch_my_endpoint(self, response):
            return response

    example_session = {'session_cookie': 'MY_COOKIE'}
    client = MyClient(example_session)
    r = client.fetch_my_endpoint()

    assert r == example_note
    get_request_fn(mock_requests).assert_called_once_with(
        'GET', f'{example_url}/my-endpoint', timeout=None,
        cookies=example_session
    )
