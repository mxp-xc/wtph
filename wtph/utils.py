# -*- coding: utf-8 -*-
# @Time: 2021/8/15 16:34
import dataclasses
import inspect
import re
from collections import OrderedDict
from enum import Enum
from typing import Type, Optional, Callable, TYPE_CHECKING, Tuple, List, Dict

from pydantic import create_model, BaseConfig, BaseModel
from pydantic.fields import ModelField
from pydantic.fields import (
    SHAPE_SET, SHAPE_TUPLE, SHAPE_SEQUENCE, SHAPE_TUPLE_ELLIPSIS, SHAPE_LIST, SHAPE_SINGLETON
)
from pydantic.utils import lenient_issubclass
from .params import Query, Form, Body, Depends

if TYPE_CHECKING:
    from pydantic.main import Model  # noqa

_empty = inspect.Parameter.empty

SUPPORT_PARAMS = {Query, Form, Body, Depends}

sequence_shapes = {
    SHAPE_LIST,
    SHAPE_SET,
    SHAPE_TUPLE,
    SHAPE_SEQUENCE,
    SHAPE_TUPLE_ELLIPSIS,
}
sequence_types = (list, set, tuple)


def get_name(obj: Callable) -> str:
    try:
        return obj.__name__
    except AttributeError:
        return obj.__class__.__name__  # noqa


def generate_model_from_callable(
        f: Callable,
        skip_first_argument: bool = False,
        *,
        model_name=None,
        config: Optional[Type[BaseConfig]] = None,
) -> Tuple[Type["Model"], Dict[str, Depends]]:
    """从解析视图函数中的参数, 生成校验的Type[BaseModel]

    :param f: 视图函数
    :param skip_first_argument: 是否跳过第一个参数
    :param model_name: model名称, 可选常数字符串, 一个format的字符串, 和一个函数, 接受当前函数的参数
    :param config: 生成的model的配置
    :return 非依赖解析的model与依赖model
    """
    sig = inspect.signature(f)

    if skip_first_argument:
        items = list(sig.parameters.items())
        parameters = OrderedDict(items[1:])
    else:
        parameters = sig.parameters

    model_fields = {}
    name_depend_map = {}

    for name, param in parameters.items():
        if param.annotation is _empty:
            continue
            # raise TypeError("%s arg: %s missing annotation" % (get_name(f), name))
        if param.default is _empty:
            raise ValueError("%s arg: %s not specified default" % (get_name(f), name))

        param_class = param.default.__class__

        if param_class is Depends:
            name_depend_map[name] = param.default
            continue

        if param_class not in SUPPORT_PARAMS:
            raise ValueError("not support type: %s, only support: %s" % (param.default.__class__, SUPPORT_PARAMS))
        model_fields[name] = (param.annotation, param.default)
    if model_name is None:
        model_name = "RequestValidateModel<for: '%s'>" % (get_name(f))
    elif isinstance(model_name, str):
        model_name = model_name.format(name=get_name(f))
    else:
        assert callable(model_name), "model name must None str or callable"
        model_name = model_name(f)

    model = create_model(
        model_name,
        __config__=config,
        __module__=f.__module__,  # noqa
        **model_fields
    )
    return model, name_depend_map


# 下面的与是从FastAPI中复制过来, is_scalar_sequence_field用于检测一个ModelField是否是一个序列类型
# 对于序列类型, 需要调用对应的getlist

def is_scalar_field(field: ModelField) -> bool:
    field_info = field.field_info
    if not (
            field.shape == SHAPE_SINGLETON
            and not lenient_issubclass(field.type_, BaseModel)
            and not lenient_issubclass(field.type_, sequence_types + (dict,))
            and not dataclasses.is_dataclass(field.type_)
            and not isinstance(field_info, Body)
    ):
        return False
    if field.sub_fields:
        if not all(is_scalar_field(f) for f in field.sub_fields):
            return False
    return True


def is_scalar_sequence_field(field: ModelField) -> bool:
    if (field.shape in sequence_shapes) and not lenient_issubclass(
            field.type_, BaseModel
    ):
        if field.sub_fields is not None:
            for sub_field in field.sub_fields:
                if not is_scalar_field(sub_field):
                    return False
        return True
    if lenient_issubclass(field.type_, sequence_types):
        return True
    return False


def _replace_constraint_name(name):
    def _repl(match_: re.Match):
        return match_.groups()[0].lower()

    return re.sub("Constrained(.*?)Value", _repl, name)


def to_chinese(field: ModelField):
    """将字段以中文输出, 包含类型, 限制条件, 描述"""
    display: str = field._type_display()  # noqa
    display = _replace_constraint_name(display)
    constraint = []
    if field.required:
        constraint.append("required")
    else:
        if lenient_issubclass(field.type_, Enum) and isinstance(field.default, Enum):
            value = field.default.value
        else:
            value = field.default
        if isinstance(value, str):
            value = "'%s'" % value
        constraint.append("默认值为 %s" % value)
    field_info = field.field_info
    field_constraints = field_info.get_constraints()

    if (
            "gt" in field_constraints or "ge" in field_constraints or
            "le" in field_constraints or "lt" in field_constraints
    ):
        if (
                ("gt" in field_constraints or "ge" in field_constraints) and
                ("le" in field_constraints or "lt" in field_constraints)
        ):
            if "lt" in field_constraints:
                right = "< %s" % field_info.lt
            else:
                right = "<= %s" % field_info.le

            if "gt" in field_constraints:
                left = "%s <" % field_info.gt
            else:
                left = "%s <=" % field_info.ge
            constraint.append("%s x %s" % (left, right))
        elif "gt" in field_constraints or "ge" in field_constraints:
            if "gt" in field_constraints:
                constraint.append("x > %s" % field_info.gt)
            else:
                constraint.append("x >= %s" % field_info.ge)
        else:
            if "lt" in field_constraints:
                constraint.append("x < %s" % field_info.lt)
            else:
                constraint.append("x <= %s" % field_info.le)

    if "max_length" in field_constraints or "min_length" in field_constraints:
        if "max_length" in field_constraints and "min_length" in field_constraints:
            if field_info.max_length == field_info.min_length:
                constraint.append("长度为%s" % field_info.max_length)
            else:
                constraint.append("%s <= 长度 <= %s" % (field_info.min_length, field_info.max_length))
        elif "max_length" in field_constraints:
            constraint.append("长度 <= %s" % field_info.max_length)
        else:
            constraint.append("长度 >= %s" % field_info.min_length)

    if "regex" in field_constraints:
        constraint.append("regex: %s" % field_info.regex)

    if lenient_issubclass(field.type_, Enum):
        constraint.append("可选值为 %s" % set(field.type_._value2member_map_.keys()))  # noqa

    return display, constraint
