Type Checking
=============

You should be able to use *mypy* and other type checkers to verify the
correctness of your code. The library itself is checked with the ``--strict``
flag.

For the most part, you should not have issues with type checking except when
passing keyword arguments to your endpoints. Unfortunately you will see the
following error.

::

     error: Unexpected keyword argument "arg" for "call" of "Client"
     [call-arg]

This is due to inherent limitations with the typing spec as of Python 3.12,
and the fact that keyword arguments cannot be concatenated for type checking
purposes. For more information, see `pep`_ 612.

.. _pep: https://peps.python.org/pep-0612/#concatenating-keyword-parameters

Mitigations
-----------

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
