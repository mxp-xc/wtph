# -*- coding: utf-8 -*-
# @Time: 2021/9/22 12:23
import asyncio
import typing as t
from functools import wraps

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
            inject = flask_inject
        else:
            msg = "Don't support mode: '%s', only support mode: %s" \
                  " you can customize by config.customize_setup()" % (mode, SUPPORT_MODE)

            raise ConfigError(msg)
        self.customize_setup(parser_factory, inject=inject, inject_extra=inject_extra)  # noqa


config = Config()


def flask_inject(
        cfg: Config,
        openapi_url: t.Optional[str] = "/openapi.json",
        docs_url: t.Optional[str] = "/docs",
        openapi_extra: t.Optional[dict] = None,
        swagger_extra: t.Optional[dict] = None,
):
    from flask import Flask
    from .openapi import get_openapi
    from .openapi.docs import get_swagger_ui_html
    flask_add_url_rule = Flask.add_url_rule

    @wraps(flask_add_url_rule)
    def add_url_rule(
            app: Flask,
            rule: str,
            endpoint: t.Optional[str] = None,
            view_func: t.Optional[t.Callable] = None,
            methods: t.Optional[t.Iterable[str]] = None,
            view_config: t.Optional[dict] = None,
            **options,
    ):
        if methods is not None and view_func is not None:
            methods = set(methods)
            vc: View
            if asyncio.iscoroutinefunction(view_func):
                vc = cfg.async_view_class
            else:
                vc = cfg.view_class
            view_func = vc(endpoint=view_func, path=rule, methods=methods, **(view_config or {})).partial()
        return flask_add_url_rule(app, rule, endpoint, view_func, methods=methods, **options)

    Flask.add_url_rule = add_url_rule

    flask_app: Flask = cfg.app
    if flask_app is not None:
        if openapi_url:
            openapi_extra = openapi_extra or {}
            openapi_extra.setdefault('title', 'flask')
            openapi_extra.setdefault('version', '0.1')
            openapi_json = None

            @flask_app.get(openapi_url, view_config={"include_in_schema": False})
            def get_openapi_json():
                nonlocal openapi_json
                if openapi_json is not None:
                    return openapi_json
                openapi_json = get_openapi(**openapi_extra)
                return openapi_json

        if openapi_url and docs_url:
            swagger_extra = swagger_extra or {}
            swagger_extra.setdefault("title", "flask")

            @flask_app.get(docs_url, view_config={"include_in_schema": False})
            def get_docs():
                return get_swagger_ui_html(openapi_url, **swagger_extra)
