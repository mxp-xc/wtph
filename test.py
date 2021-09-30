# -*- coding: utf-8 -*-
# @Time: 2021/8/15 18:46
from pprint import pprint
from enum import Enum
from typing import List
from pydantic import BaseModel, Field
from pydantic.fields import ModelField
from pydantic.schema import *
from type_check.utils import to_chinese
from pprint import pprint
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi, get_model_definitions
from fastapi.dependencies.utils import solve_dependencies


class TalkType(Enum):
    type1 = "123"
    type2 = "234"


class Test(BaseModel):
    pass


class Password(BaseModel):
    value: str
    alg: str
    tst: Test


class User(BaseModel):
    talk_type: TalkType
    pwd: Password
    a1: List[Test]
    a2: int = Field(100, ge=50, le=200)
    list1: list = Field([])
    str1: str = Field("123", min_length=10, max_length=100, regex="abc.*?")


pwd = User.__fields__['pwd']
f1 = User.__fields__['str1']

# pprint(model_schema(Test))
# pprint(schema([Test]))
ms = get_flat_models_from_model(
    User,
    known_models=set(),
)
ms.discard(User)

model_name_map = get_model_name_map(ms)
pprint(get_model_definitions(flat_models=ms, model_name_map=model_name_map))
