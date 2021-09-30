# -*- coding: utf-8 -*-
# @Time: 2021/9/30 21:58
import asyncio
import typing as t
from functools import wraps

from flask import Flask

from .base import BaseAppTypeHint

if t.TYPE_CHECKING:
    from wtph import View
    from wtph.config import Config


def flask_inject(
        cfg: "Config",
        openapi_url: t.Optional[str] = "/openapi.json",
        docs_url: t.Optional[str] = "/docs",
        openapi_extra: t.Optional[dict] = None,
        swagger_extra: t.Optional[dict] = None,
):
    from flask import Flask
    from ..openapi import get_openapi
    from ..openapi.docs import get_swagger_ui_html
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
            vc: "View"
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


def type_hint(app) -> "FlaskTypeHint":
    return app


class FlaskTypeHint(Flask, BaseAppTypeHint):
    def get(
            self,
            rule: str,
            view_config: t.Optional[dict] = None,
            **options,
    ) -> t.Callable:
        pass

    def post(
            self,
            rule: str,
            view_config: t.Optional[dict] = None,
            **options,
    ) -> t.Callable:
        pass

    def put(
            self,
            rule: str,
            view_config: t.Optional[dict] = None,
            **options,
    ) -> t.Callable:
        pass

    def delete(
            self,
            rule: str,
            view_config: t.Optional[dict] = None,
            **options,
    ) -> t.Callable:
        pass

    def patch(
            self,
            rule: str,
            view_config: t.Optional[dict] = None,
            **options,
    ) -> t.Callable:
        pass

    def route(
            self,
            rule: str,
            view_config: t.Optional[dict] = None,
            **options,
    ) -> t.Callable:
        pass

    def add_url_rule(
            self,
            rule: str,
            endpoint: t.Optional[str] = None,
            view_func: t.Optional[t.Callable] = None,
            view_config: t.Optional[dict] = None,
            **options: t.Any,
    ):
        pass
