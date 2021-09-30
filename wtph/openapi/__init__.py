# -*- coding: utf-8 -*-
# @Time: 2021/9/21 13:36
from collections import defaultdict
from typing import Optional, Dict, Any, Union, List, Iterable

from pydantic.schema import get_model_name_map

from .utils import (
    OpenapiPathHandler,
    get_views_flat_models,
    get_views_models_definitions
)
from ..view import View


def get_openapi(
        *,
        title: str,
        version: str,
        views: Optional[Iterable[View]] = None,
        openapi_version: str = "3.0.2",
        description: Optional[str] = None,
        tags: Optional[List[Dict[str, Any]]] = None,
        servers: Optional[List[Dict[str, Union[str, Any]]]] = None,
        terms_of_service: Optional[str] = None,
        contact: Optional[Dict[str, Union[str, Any]]] = None,
        license_info: Optional[Dict[str, Union[str, Any]]] = None,
):
    info = {"title": title, "version": version}
    output: Dict[str, Any] = {"openapi": openapi_version, "info": info}
    if description:
        info["description"] = description
    if terms_of_service:
        info["termsOfService"] = terms_of_service
    if contact:
        info["contact"] = contact
    if license_info:
        info["license"] = license_info
    if servers:
        output["servers"] = servers
    if tags:
        output["tags"] = tags
    if views is None:
        from ..view import view_set as views
    components: Dict[str, Dict[str, Any]] = {}
    flat_models = get_views_flat_models(views)
    model_name_map = get_model_name_map(flat_models)
    definitions = get_views_models_definitions(flat_models, model_name_map)
    paths: Dict[str, Dict[str, Any]] = defaultdict(dict)
    for view in views:
        path = OpenapiPathHandler(view, model_name_map).get_openapi_path()
        if path:
            paths[view.path].update(path)
    if definitions:
        components["schemas"] = {k: definitions[k] for k in sorted(definitions)}
    if components:
        output["components"] = components
    output["paths"] = paths
    return output
