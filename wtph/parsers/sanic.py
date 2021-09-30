# -*- coding: utf-8 -*-
# @Time: 2021/9/30 23:44
from sanic import Request
from sanic.request import RequestParameters

from .base import ParserManagerFactory, BaseMultiItemParser
from ..params import Query

sanic_parser_manager_factory = ParserManagerFactory()


@sanic_parser_manager_factory.register_parser
class SanicQueryParser(BaseMultiItemParser):
    param_class = Query
    single_get = staticmethod(lambda args, key: args[key][0])
    multi_get = staticmethod(lambda args, key: args[key])

    def parse(self, request: Request):
        data = {}
        args = request.args
        for field, getter in self.field_getters:
            if field.alias in args:
                data[field.alias] = getter(args, field.alias)

        return data
