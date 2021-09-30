# -*- coding: utf-8 -*-
# @Time: 2021/9/30 21:59
import asyncio
import typing as t
from functools import wraps
from typing import Optional, Iterable, Union, List

from sanic import Sanic

from .base import BaseAppTypeHint

if t.TYPE_CHECKING:
    from wtph import View
    from wtph.config import Config


def sanic_inject(
        cfg: "Config",
        openapi_url: t.Optional[str] = "/openapi.json",
        docs_url: t.Optional[str] = "/docs",
        openapi_extra: t.Optional[dict] = None,
        swagger_extra: t.Optional[dict] = None,
):
    from sanic.mixins.routes import RouteMixin
    from ..openapi import get_openapi
    from ..openapi.docs import get_swagger_ui_html
    sanic_route = RouteMixin.route

    @wraps(sanic_route)
    def route(
            app: Sanic,
            uri: str,
            methods: t.Optional[t.Iterable[str]] = None,
            view_config: t.Optional[dict] = None,
            **options,
    ):
        def wrapper(handler):
            if methods is not None:
                methods_ = frozenset(methods)
                vc: "View"
                if asyncio.iscoroutinefunction(methods_):
                    vc = cfg.async_view_class
                else:
                    vc = cfg.view_class
                handler = vc(endpoint=handler, path=uri, methods=methods, **(view_config or {})).partial()
            return sanic_route(app, uri, methods, **options)(handler)

        return wrapper

    RouteMixin.route = route

    sanic_app: SanicTypeHint = cfg.app
    if sanic_app is not None:
        if openapi_url:
            openapi_extra = openapi_extra or {}
            openapi_extra.setdefault('title', 'sanic')
            openapi_extra.setdefault('version', '0.1')
            openapi_json = None

            @sanic_app.get(openapi_url, view_config={"include_in_schema": False})  # noqa
            def get_openapi_json():
                nonlocal openapi_json
                if openapi_json is not None:
                    return openapi_json
                openapi_json = get_openapi(**openapi_extra)
                return openapi_json

        if openapi_url and docs_url:
            swagger_extra = swagger_extra or {}
            swagger_extra.setdefault("title", "sanic")

            @sanic_app.get(docs_url, view_config={"include_in_schema": False})  # noqa
            def get_docs():
                return get_swagger_ui_html(openapi_url, **swagger_extra)


def type_hint(app):
    return app


class SanicTypeHint(Sanic, BaseAppTypeHint):
    def route(
            self,
            uri: str,
            methods: t.Optional[t.Iterable[str]] = None,
            view_config: t.Optional[dict] = None,
            **options,
    ):
        pass

    def add_route(self, handler, uri: str, methods: Iterable[str] = frozenset({"GET"}), host: Optional[str] = None,
                  strict_slashes: Optional[bool] = None, version: Optional[int] = None, name: Optional[str] = None,
                  stream: bool = False, version_prefix: str = "/v"):
        return super().add_route(handler, uri, methods, host, strict_slashes, version, name, stream, version_prefix)

    def get(self, uri: str, host: Optional[str] = None, strict_slashes: Optional[bool] = None,
            version: Optional[int] = None, name: Optional[str] = None, ignore_body: bool = True,
            version_prefix: str = "/v"):
        return super().get(uri, host, strict_slashes, version, name, ignore_body, version_prefix)

    def post(self, uri: str, host: Optional[str] = None, strict_slashes: Optional[bool] = None, stream: bool = False,
             version: Optional[int] = None, name: Optional[str] = None, version_prefix: str = "/v"):
        return super().post(uri, host, strict_slashes, stream, version, name, version_prefix)

    def put(self, uri: str, host: Optional[str] = None, strict_slashes: Optional[bool] = None, stream: bool = False,
            version: Optional[int] = None, name: Optional[str] = None, version_prefix: str = "/v"):
        return super().put(uri, host, strict_slashes, stream, version, name, version_prefix)

    def head(self, uri: str, host: Optional[str] = None, strict_slashes: Optional[bool] = None,
             version: Optional[int] = None, name: Optional[str] = None, ignore_body: bool = True,
             version_prefix: str = "/v"):
        return super().head(uri, host, strict_slashes, version, name, ignore_body, version_prefix)

    def options(self, uri: str, host: Optional[str] = None, strict_slashes: Optional[bool] = None,
                version: Optional[int] = None, name: Optional[str] = None, ignore_body: bool = True,
                version_prefix: str = "/v"):
        return super().options(uri, host, strict_slashes, version, name, ignore_body, version_prefix)

    def patch(self, uri: str, host: Optional[str] = None, strict_slashes: Optional[bool] = None, stream=False,
              version: Optional[int] = None, name: Optional[str] = None, version_prefix: str = "/v"):
        return super().patch(uri, host, strict_slashes, stream, version, name, version_prefix)

    def delete(self, uri: str, host: Optional[str] = None, strict_slashes: Optional[bool] = None,
               version: Optional[int] = None, name: Optional[str] = None, ignore_body: bool = True,
               version_prefix: str = "/v"):
        return super().delete(uri, host, strict_slashes, version, name, ignore_body, version_prefix)
