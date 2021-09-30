# -*- coding: utf-8 -*-
# @Time: 2021/9/21 14:20
import itertools
from typing import Iterable
from enum import Enum

from pydantic.schema import get_flat_models_from_model, model_process_schema
from pydantic.schema import TypeModelSet, TypeModelOrEnum

from ..view import View
from ..parsers.base import ParserManager


def get_name(f) -> str:
    try:
        return f.__name__
    except AttributeError:
        return f.__class__.__name__


def get_depend_model_field(manager: ParserManager):
    for parser in manager.depend_parsers:
        yield from parser.model.__fields__.values()
        if parser.has_depend_parser():
            yield from get_depend_model_field(parser)


class OpenapiPathHandler(object):
    def __init__(self, view: View, model_name_map: dict, ref_prefix: str = "#/components/schemas/"):
        self.view = view
        self.model_name_map = model_name_map
        self.ref_prefix = ref_prefix

    def model_process_schema(self, model: TypeModelOrEnum):
        return model_process_schema(model, model_name_map=self.model_name_map)

    def get_path_operation_metadata(self, method: str):
        view = self.view
        operation = {}
        if view.tags:
            operation["tags"] = view.tags
        operation['summary'] = view.summary if view.summary else view.name.replace("_", " ").title()  # noqa

        if view.description:
            operation["description"] = view.description
        operation["operationId"] = view.name + view.path + "_" + method.lower()
        if view.deprecated:
            operation["deprecated"] = view.deprecated
        return operation

    def get_parser_manager_properties(
            self,
            manager: ParserManager,
    ) -> dict:
        schema = model_process_schema(
            manager.model,
            model_name_map=self.model_name_map,
            ref_prefix=self.ref_prefix
        )[0]
        properties: dict = schema['properties']
        for parser in self.view.parser_manager.depend_parsers:
            schema = self.model_process_schema(parser.model)[0]
            properties.update(schema['properties'])

        return properties

    def get_parameters_from_parser_manager(self, manager: ParserManager):
        parameters = []
        properties = self.get_parser_manager_properties(manager)
        for field in itertools.chain(manager.model.__fields__.values(), get_depend_model_field(manager)):
            field_info = field.field_info
            if not hasattr(field_info, "in_"):
                continue
            in_ = field_info.in_  # noqa
            if isinstance(in_, Enum):
                in_ = in_.value
            name = field.alias
            parameters.append({
                "name": name,
                "in": in_,
                "required": field.required,
                "schema": properties[name]
            })

        return parameters

    def get_openapi_path(self):
        view = self.view
        if not view.include_in_schema and view.path is not None:
            return
        path = {}
        for method in view.methods:
            method = method.lower()
            operation = self.get_path_operation_metadata(method)
            operation['parameters'] = self.get_parameters_from_parser_manager(view.parser_manager)
            operation['responses'] = {
                "200": {
                    "description": "Successful Response",
                }
            }

            path[method] = operation
        return path


def get_views_flat_models(views: Iterable[View]):
    flag_models = set()
    for view in views:
        flag_models |= get_flat_models_from_model(view.parser_manager.model)

    return flag_models


def get_views_models_definitions(flat_models: TypeModelSet, model_name_map: dict):
    definitions = {}
    for model in flat_models:
        m_schema, m_definitions, m_nested_models = model_process_schema(
            model, model_name_map=model_name_map, ref_prefix="#/components/schemas/"
        )
        definitions.update(m_definitions)
        model_name = model_name_map[model]
        definitions[model_name] = m_schema
    return definitions
