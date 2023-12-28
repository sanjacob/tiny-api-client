Testing Guide
=============

Testing an API client written with ``tiny-api-client`` is not straightforward out of the box.
The reason for this is that decorators cannot be patched after the functions they decorate
have been imported. To remediate this issue, a companion pytest plugin is available.

Installation
------------

::

    pip install pytest-tiny-api-client

Testing Fixture
---------------

This plugin exposes a pytest fixture ``api_call``, which replaces
the usual implementation of the api decorators.
Thus, your api endpoints will receive the return value of this fixture as
their response argument, instead of the actual api result.

The fixture is an instance of ``unittest.mock.Mock``.
This mock accepts an *endpoint* argument, and arbitrary keyword arguments, which
are passed directly from the method decorator of your endpoint definition.
Thus, you can use the `mock`_ assertions to check that your endpoint is passing
the right arguments to the decorator.

.. _mock: https://docs.python.org/3/library/unittest.mock.html#unittest.mock.Mock


Usage
-----

::

    from my_api import MyClient
 
    def test_my_client(api_call):
        # set your fake api response
        api_call.return_value = [{"id": 0, "name": "Mary Jane"}, ...]
        # make your calls
        client = MyClient()
        users = client.fetch_users()
        # make assertions
        assert users[0].name == "Mary Jane"


Not Using Pytest
----------------

If you are not using pytest, or you don't want to use the plugin, all you have to
do is to patch ``tiny_api_client.{method}`` where method is one of the http method
decorators. This patch must occur before your api module is imported.
Another option is to call ``importlib.reload(module)`` where module is your api module.

For more information on how to do this, check this `stackoverflow`_ question.
By far easier, though, is to see how this plugin is implemented, and replicate this
behaviour in your own project.

.. _stackoverflow: https://stackoverflow.com/questions/7667567/can-i-patch-a-python-decorator-before-it-wraps-a-function
