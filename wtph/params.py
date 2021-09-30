from enum import Enum
from typing import Any, Dict, Optional, Callable

from pydantic.fields import FieldInfo, Undefined


# same from fastapi.params.py

class ParamTypes(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"


class Param(FieldInfo):
    in_: ParamTypes
    media_type = None

    def __init__(
            self,
            default: Any,
            *,
            alias: Optional[str] = None,
            title: Optional[str] = None,
            description: Optional[str] = None,
            gt: Optional[float] = None,
            ge: Optional[float] = None,
            lt: Optional[float] = None,
            le: Optional[float] = None,
            min_length: Optional[int] = None,
            max_length: Optional[int] = None,
            regex: Optional[str] = None,
            example: Any = Undefined,
            examples: Optional[Dict[str, Any]] = None,
            deprecated: Optional[bool] = None,
            **extra: Any,
    ):
        self.deprecated = deprecated
        self.example = example
        self.examples = examples
        super().__init__(
            default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            **extra,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Query(Param):
    in_ = ParamTypes.query


class Body(Param):
    pass


class Form(Body):
    pass


class Depends:
    def __init__(
            self, dependency: Callable[..., Any], *, use_cache: bool = True
    ):
        self.dependency = dependency
        self.use_cache = use_cache

    def __repr__(self) -> str:
        attr = getattr(self.dependency, "__name__", type(self.dependency).__name__)
        cache = "" if self.use_cache else ", use_cache=False"
        return f"{self.__class__.__name__}({attr}{cache})"
