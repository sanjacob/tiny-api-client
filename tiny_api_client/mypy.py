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
from typing import NamedTuple
from collections.abc import Callable, Iterable

from mypy.nodes import ARG_NAMED, ARG_NAMED_OPT, StrExpr
from mypy.options import Options
from mypy.plugin import MethodContext, Plugin
from mypy.types import Type, CallableType


class RouteParser:
    formatter = string.Formatter()

    class FormatTuple(NamedTuple):
        literal_text: str | None
        field_name: str | None
        format_spec: str | None
        conversion: str | None

    def __init__(self, route: str):
        parsed = self.formatter.parse(route)
        self.params = []

        for t in parsed:
            self.params.append(self.FormatTuple(*t))

    @property
    def fields(self) -> Iterable[str]:
        return (x.field_name for x in self.params if x.field_name is not None)

    @property
    def has_optional(self) -> bool:
        if not len(self.params):
            return False
        return self.params[-1].field_name is not None


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
        self._ctx_cache: dict[str, RouteParser] = {}
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
        if len(ctx.args) and len(ctx.args[0]):
            pos = f"{ctx.context.line},{ctx.context.column}"
            route = ctx.args[0][0]
            assert isinstance(route, StrExpr)
            self._ctx_cache[pos] = RouteParser(route.value)
        return ctx.default_return_type

    def _decorator_callback(self, ctx: MethodContext) -> Type:
        """Append route positional parameters to function kw-only args.

        The route parameters are retrieved from memory according to the
        context, and they are included in the decorated function type
        as optional keyword-only parameters.
        """
        pos = f"{ctx.context.line},{ctx.context.column}"
        default_ret = ctx.default_return_type
        # need this to access properties without a warning
        assert isinstance(default_ret, CallableType)

        # Modify default return type in place (probably fine)
        route_parser = self._ctx_cache[pos]
        for p in route_parser.fields:
            default_ret.arg_types.append(
                # API endpoint URL params must be strings
                ctx.api.named_generic_type("builtins.str", [])
            )
            default_ret.arg_kinds.append(ARG_NAMED)
            default_ret.arg_names.append(p)

        if route_parser.has_optional:
            default_ret.arg_kinds[-1] = ARG_NAMED_OPT

        return ctx.default_return_type


def plugin(version: str) -> type[Plugin]:
    return TinyAPIClientPlugin
