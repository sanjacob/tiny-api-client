"""
mypy plugin for tiny-api-client.

Please activate in your mypy configuration file.
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

import string
from collections.abc import Callable

from mypy.nodes import ARG_NAMED_OPT, StrExpr
from mypy.options import Options
from mypy.plugin import MethodContext, Plugin
from mypy.types import Type, CallableType


class TinyAPIClientPlugin(Plugin):
    """Companion mypy plugin for tiny-api-client.

    Normally, it isn't possible to type check route parameters since
    they are defined at runtime, and typing primitives are not capable
    of introspection.

    This plugin captures the route parameters of every endpoint and
    modifies the decorated signature to include said parameters as if
    they were factual ones.
    """
    def __init__(self, options: Options) -> None:
        self._ctx_cache: dict[str, list[str]] = {}
        super().__init__(options)

    def get_method_hook(self, fullname: str
                        ) -> Callable[[MethodContext], Type] | None:
        if fullname == "tiny_api_client.DecoratorFactory.__call__":
            return self._factory_callback
        if fullname == "tiny_api_client.RequestDecorator.__call__":
            return self._decorator_callback
        return None

    def _factory_callback(self, ctx: MethodContext) -> Type:
        """Capture route positional params passed in decorator factory.

        The route argument is captured and parsed for positional
        parameters. These parameters are stored in a dictionary
        with the line and column as its key.

        The parameters are later retrieved in a subsequent call
        to the returned decorator.
        """
        if len(ctx.args) > 0:
            pos = f"{ctx.context.line},{ctx.context.column}"
            route_params = []
            formatter = string.Formatter()
            route = ctx.args[0][0]
            assert isinstance(route, StrExpr)

            for x in formatter.parse(route.value):
                if x[1] is not None:
                    route_params.append(x[1])
            self._ctx_cache[pos] = route_params
        return ctx.default_return_type

    def _decorator_callback(self, ctx: MethodContext) -> Type:
        """Append route positional parameters to function kw-only args.

        The route parameters are retrieved from memory according to the
        context, and they are included in the decorated function type
        as optional keyword-only parameters.
        """
        pos = f"{ctx.context.line},{ctx.context.column}"
        default_ret = ctx.default_return_type
        assert isinstance(default_ret, CallableType)

        # Modify default return type in place (probably fine)
        for p in self._ctx_cache[pos]:
            default_ret.arg_types.append(
                # Since the URL is a string, type of arguments
                # should also be string
                ctx.api.named_generic_type("builtins.str", [])
            )
            default_ret.arg_kinds.append(ARG_NAMED_OPT)
            default_ret.arg_names.append(p)

        return ctx.default_return_type


def plugin(version: str) -> type[Plugin]:
    return TinyAPIClientPlugin
