# Tiny API Client 🐝

[![License: GPL  v2][license-shield]][gnu]

Write JSON API Clients in Python without the fluff, pumped full of syntactic sugar

```python
from tiny_api_client import api_client, get, post, delete

@api_client('https://example.org/api/public/v{version}')
class MyAPIClient:
	@get('/users/{user_id}')
	def find_user(self, response):
		return response

	@post('/notes')
	def create_note(self, response):
		return response

	@delete('/notes/{note_id}/attachment/{attachment_id}', version=3)
	def delete_note_attachment(self, response):
		return response

>>> client = MyClient()
>>> client.find_user(user_id='PeterParker')
{'name': 'Peter', 'surname': 'Parker', ...}
>>> client.create_note(data={'title': 'My New Note', 'content': 'Hello World!'})
{'id': ...}
>>> client.delete_note_attachment(node_id=...)
```



## Features

- Instance-scoped `requests.Session()` with connection pooling and cookie preservation
- JSON is king, but XML and raw responses are fine too
- Endpoints can use GET, POST, PUT, PATCH, DELETE
- Route parameters are optional
- Easy integration with your custom API classes
- Declare endpoints under different API versions
- Can define the API URL at runtime if not available before
- Can set a custom CookieJar to pass with all requests
- Pass along any parameters you would usually pass to requests
- Custom JSON status error handling



## Installation

```bash
pip install tiny-api-client
```



## Documentation

You can find the documentation at https://tiny-api-client.readthedocs.io



## License

[![License: LGPL  v2.1][license-shield]][gnu]

This software is distributed under the [Lesser General Public License v2.1][license], more information available at the [Free Software Foundation][gnu].



<!-- LICENSE -->

[license]: LICENSE "Lesser General Public License v2.1"
[gnu]: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html "Free Software Foundation"
[license-shield]: https://img.shields.io/github/license/sanjacob/tiny-api-client



<!-- SHIELD LINKS -->

[pypi]: https://pypi.org/project/tiny-api-client



<!-- SHIELDS -->

[pypi-shield]: https://img.shields.io/pypi/v/tiny-api-client
[build-shield]: https://img.shields.io/github/actions/workflow/status/sanjacob/tiny-api-client/build.yml?branch=master
[docs-shield]: https://img.shields.io/readthedocs/tiny-api-client
