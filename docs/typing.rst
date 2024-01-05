Type Checking
=============

Due to the way route parameters are declared with tiny-api-client,
type checking them would be impossible for tools like *mypy* without
knowledge of how this library works.
Therefore, it was necessary to go beyond ordinary type annotations.


mypy Plugin
-----------

As of version ``>=1.2.1``, the library ships with a mypy plugin that
can parse positional route parameters declared in your endpoints and
treat them as keyword-only optional string parameters.

Therefore, errors like this will be highlighted:

::

    @get('/users/{user_id}/')
    def find_user(self, response: dict[str, str]) -> User:
        ...

    client.find_user(user_name="username")

    >>> error: Unexpected keyword argument "user_name" for "find_user"
        of "MyClient"  [call-arg]

.. note::
   The mypy plugin is still in early development, and may not have all
   expected features. Additional requests parameters in endpoint calls
   are not supported yet.

To enable the plugin, add this to your pyproject.toml, or check the
`mypy_config`_ documentation if you are using a different file format.

::

    [mypy]
    plugins = ["tiny_api_client.mypy"]


.. _mypy_config: https://mypy.readthedocs.io/en/latest/config_file.html


Without Plugin
--------------

It is possible to type check an API client without the plugin, but be
warned that you won't have positional route parameter checking
whatsoever.

The major issue you will run into is the following:

::

    client.my_call(my_arg="...")

    error: Unexpected keyword argument "my_arg" for "my_call"
    of "Client" [call-arg]

Due to inherent limitations with the typing spec as of Python 3.12, it
is not possible to add arbitrary keyword-only arguments to a decorated
function for type checking purposes. For more information, see
`pep`_ 612.

.. _pep: https://peps.python.org/pep-0612/#concatenating-keyword-parameters

One way around this is to include arbitrary keyword-only arguments in your
endpoint definition. This will let mypy know that the wrapper function can
also accept arbitrary keyword-only arguments. The obvious downside is that
it does not look very clean and if you have multiple endpoints it can get
tiring to write them like this.

::

    from typing import Any

    @get('/my_endpoint/{item_id}')
    def my_call(self, response, /, **_: Any) -> str:
        return response

The other way is to manually silence this error for a certain scope.
For more information, see the `mypy`_ docs.

.. _mypy: https://mypy.readthedocs.io/en/stable/error_codes.html
