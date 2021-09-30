# -*- coding: utf-8 -*-
# @Time: 2021/8/13 21:15
import typing as t

from .params import Query, Form, Body, Depends
from .parsers.base import ParserManagerFactory
from .utils import get_name, generate_model_from_callable
from .openapi import get_openapi
from .openapi.docs import get_swagger_ui_html
from .view import View, api


def setup_wtph(
        mode: str,
        openapi_url: t.Optional[str] = "/openapi.json",
        docs_url: t.Optional[str] = "/docs",
        openapi_extra: t.Optional[dict] = None,
        swagger_extra: t.Optional[dict] = None,
        app=None
):  # noqa
    from .config import config
    config.setup(
        mode=mode,
        openapi_url=openapi_url,
        docs_url=docs_url,
        openapi_extra=openapi_extra,
        swagger_extra=swagger_extra,
        app=app,
    )
