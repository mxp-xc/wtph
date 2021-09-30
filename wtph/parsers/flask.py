# -*- coding: utf-8 -*-
# @Time: 2021/8/17 21:52
from flask import request

from .base import ParserManagerFactory, Parser, BaseMultiItemParser
from ..params import Query, Body, Form

flask_parser_manager_factory = ParserManagerFactory()


@flask_parser_manager_factory.register_parser
class FlaskQueryParser(BaseMultiItemParser):
    param_class = Query

    def parse(self):
        data = {}
        args = request.args
        for field, getter in self.field_getters:
            if field.alias in args:
                data[field.alias] = getter(args, field.alias)

        return data


@flask_parser_manager_factory.register_parser
class FlaskFormParser(BaseMultiItemParser):
    param_class = Form

    def parse(self):
        data = {}
        form = request.form
        for field, getter in self.field_getters:
            if field.alias in form:
                data[field.alias] = getter(form, field.alias)

        return data


@flask_parser_manager_factory.register_parser
class FlaskBodyParser(Parser):
    param_class = Body

    def parse(self):
        data = {}
        rj = request.json
        if rj is None:
            return {}
        for field in self.fields:
            if field.alias in rj:
                data[field.alias] = rj[field.alias]
        return data
