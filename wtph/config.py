# -*- coding: utf-8 -*-
# @Time: 2021/9/22 12:23
import typing as t

from .exceptions import ConfigError

if t.TYPE_CHECKING:
    from .parsers.base import ParserManagerFactory
    from .view import View

SUPPORT_MODE = {"flask", }


class Config(object):
    def __init__(self):
        self.app = None
        self.view_class = None
        self.async_view_class = None
        self.parser_factory = None

    def _check(self):
        required = set()
        if self.view_class is None:
            required.add("view_class")
        if self.async_view_class is None:
            required.add("async_view_class")
        if self.parser_factory is None:
            required.add("parser_factory")
        if required:
            raise ConfigError("config missing: %s, do you call setup_wtph()?" % required)

    def customize_setup(
            self,
            parser_factory: "ParserManagerFactory",
            *,
            inject: t.Optional[t.Callable] = None,
            inject_extra: t.Optional[dict] = None,
            view_class: t.Optional["View"] = None,
            async_view_class: t.Optional["View"] = None
    ):
        self.parser_factory = parser_factory
        if view_class is None:
            from .view import View as view_class  # noqa
        if async_view_class is None:
            from .view import AsyncView as async_view_class  # noqa
        self.view_class = view_class
        self.async_view_class = async_view_class
        if inject is not None:
            inject(self, **(inject_extra or {}))

    def setup(
            self,
            mode: str,
            app=None,
            **inject_extra,
    ):
        self.app = app
        if mode == "flask":
            from .parsers.flask import flask_parser_manager_factory as parser_factory
            from .injects.flask import flask_inject as inject
        elif mode == "sanic":
            from .parsers.flask import flask_parser_manager_factory as parser_factory
            from injects.sanic import sanic_inject as inject
        else:
            msg = "Don't support mode: '%s', only support mode: %s" \
                  " you can customize by config.customize_setup()" % (mode, SUPPORT_MODE)

            raise ConfigError(msg)
        self.customize_setup(parser_factory, inject=inject, inject_extra=inject_extra)  # noqa


config = Config()
