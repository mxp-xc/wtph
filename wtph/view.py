# -*- coding: utf-8 -*-
# @Time: 2021/9/21 14:11
import functools
import asyncio
from types import MethodType
from typing import Callable, Optional, Type, Iterable, List

from flask import jsonify

from .parsers.base import ParserManagerFactory, generate_model_from_callable, ParserManager
from .utils import get_name
from .config import config

view_set = set()


class View(object):
    def __init__(
            self,
            *,
            endpoint: Callable,
            path: str,
            methods: Iterable[str],
            tags: Optional[List[str]] = None,
            include_in_schema: bool = True,
            name: Optional[str] = None,
            summary: Optional[str] = None,
            deprecated: bool = False,
            parser_factory: Optional[ParserManagerFactory] = None,
            is_method: bool = False,
            description: Optional[str] = None,
    ):
        if parser_factory is None:
            assert config.parser_factory is not None
            parser_factory = config.parser_factory
        if path is None:
            include_in_schema = False
        self.path = path
        self.methods = set(methods) if methods is not None else None
        self.deprecated = deprecated
        self.include_in_schema = include_in_schema
        self.summary = summary
        self.tags = tags
        self.description = description
        self.endpoint = endpoint
        self.is_method = is_method
        model_name = "RequestValidateModel<for %s" % path
        if self.methods is not None:
            if len(self.methods) == 1:
                methods = list(self.methods)[0]
            else:
                methods = sorted(self.methods)
            model_name += ", methods=%s" % methods
        model_name += ">"
        model, depend_funcs = generate_model_from_callable(
            endpoint,
            is_method,
            model_name=model_name
        )
        self.model = model
        self.parser_manager: ParserManager = parser_factory(self.model, depend_funcs)
        if name is None:
            self.name = get_name(endpoint)
        else:
            self.name = name
        functools.update_wrapper(self, endpoint)
        if path is not None:
            view_set.add(self)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return MethodType(self.__call__, instance)

    def __hash__(self):
        if self.path is None:
            return super().__hash__()
        flag = self.path + "_".join(sorted(self.methods))
        return hash(flag)

    def __call__(self, *args, **kwargs):
        values, errors = self.parser_manager.parse(*args, __depend_cache__={}, **kwargs)
        if errors:
            return self.validate_error_handler(errors)
        kwargs.update(values)
        return self.endpoint(*args, **kwargs)

    def default_validate_error_handler(self, errors):  # noqa
        return jsonify(errors)

    validate_error_handler = default_validate_error_handler


class AsyncView(View):
    async def __call__(self, *args, **kwargs):
        values, errors = await self.parser_manager.parse(*args, __depend_cache__={}, **kwargs)
        if errors:
            return self.validate_error_handler(errors)
        kwargs.update(values)
        return self.endpoint(*args, **kwargs)


def api(
        path: Optional[str] = None,
        methods: Optional[Iterable[str]] = None,
        tags: Optional[List[str]] = None,
        is_method: bool = False,
        name: Optional[str] = None,
        summary: Optional[str] = None,
        deprecated: bool = False,
        parser_factory: Optional[ParserManagerFactory] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        view_class: Type[View] = View,
        async_view_class: Type[View] = AsyncView
):
    def wrapper(f):
        if asyncio.iscoroutinefunction(f):
            vc = AsyncView
        else:
            vc = view_class
        return vc(
            endpoint=f,
            path=path,
            name=name,
            tags=tags,
            summary=summary,
            deprecated=deprecated,
            methods=methods,
            parser_factory=parser_factory,
            is_method=is_method,
            include_in_schema=include_in_schema,
            description=description
        )

    return wrapper


def validate_error_handler(handler):
    View.validate_error_handler = handler
    return handler
