# -*- coding: utf-8 -*-
# @Time: 2021/8/15 18:00
from typing import Type, List, Optional, TYPE_CHECKING, Any, Callable, Dict

from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo, ModelField

from ..utils import generate_model_from_callable, is_scalar_sequence_field, get_name
from ..params import Depends, Param

if TYPE_CHECKING:
    from pydantic.main import Model  # noqa

ParserType = Type["Parser"]


class AsyncFlagMixin(object):
    is_async: bool


def _is_subclass(obj, cls_tuple):
    return isinstance(obj, type) and issubclass(obj, cls_tuple)


def _check_parser(parser: ParserType):
    if not _is_subclass(parser, Parser):
        raise TypeError("<parser: %s> must be a subclass of Parser" % parser)
    if parser.param_class is None:
        raise TypeError("parser.param_class: '%s' must specified a param_class" % parser)
    if parser.param_class is Depends:
        raise TypeError("not specified builtin <class `Depends`> as param_class")
    if not _is_subclass(parser.param_class, FieldInfo):
        raise TypeError("parser(%s).param_class must be a subclass of FieldInfo" % parser)


class ParserManager(AsyncFlagMixin):
    is_async = False  # sync

    def __init__(
            self,
            model: Type[BaseModel],
            from_factory: "ParserManagerFactory",
            name_depend_map: Dict[str, Depends]
    ):
        self._model = model
        self._from_factory = from_factory
        self._parsers = self.get_parsers()
        self._depend_parsers: List["DependsParser"] = [
            DependsParser.from_name_depend(name, depend, self)
            for name, depend in name_depend_map.items()
        ]

    @property
    def model(self):
        return self._model

    @property
    def depend_parsers(self) -> List["DependsParser"]:
        return self._depend_parsers

    @property
    def depend_params_name(self) -> List[str]:
        return [parser.name for parser in self._depend_parsers]

    @property
    def from_factory(self) -> "ParserManagerFactory":
        return self._from_factory

    def get_parsers(
            self,
            parser_manager_factory: "ParserManagerFactory" = None
    ) -> List["Parser"]:
        parser_manager_factory = parser_manager_factory or self._from_factory
        parsers = []
        for parser_cls in parser_manager_factory.parser_classes.values():
            p = parser_cls.from_model(self._model, self)
            if p.has_parser() != 0:
                parsers.append(p)
        return parsers

    def has_parser(self) -> bool:
        return self.has_common_parser() and self.has_depend_parser()

    def has_common_parser(self) -> bool:
        return len(self._parsers) != 0

    def has_depend_parser(self) -> bool:
        return len(self._depend_parsers) != 0

    def get_parser_by_field_name(self, field_name: str):
        for parser in self._parsers:
            for field in parser.fields:
                if field.alias == field_name:
                    return parser
        return None

    def _validate(self, data):
        try:
            return self._model(**data).dict(), None
        except ValidationError as e:
            errors = e.errors()
            for err in errors:
                field_name = err['loc'][0]
                parser = self.get_parser_by_field_name(field_name)
                assert parser is not None
                err['loc'] = (parser.param_class.__name__.lower(), field_name)
            return data, errors

    def parse(self, *args, __depend_cache__, **kwargs):
        data = {}
        errors = []
        if self.has_common_parser():
            for parser in self._parsers:
                data.update(parser.parse(*args, **kwargs))
            data, errors_ = self._validate(data)
            if errors_:
                errors.extend(errors_)
        if self.has_depend_parser():
            for parser in self._depend_parsers:
                result, errors_ = parser.parse(*args, __depend_cache__=__depend_cache__, **kwargs)
                if errors_:
                    errors.extend(errors_)
                data[parser.name] = result
        return data, errors


class AsyncParserManager(ParserManager):
    is_async = True  # async

    async def parse(self, *args, __depend_cache__, **kwargs):
        data = {}
        errors = []
        if self.has_common_parser():
            for parser in self._parsers:
                if parser.is_async:
                    values = await parser.parse(*args, **kwargs)
                else:
                    values = parser.parse(*args, **kwargs)
                data.update(values)
            data, errors_ = self._validate(data)
            if errors_:
                errors.extend(errors_)

        if self.has_depend_parser():
            for parser in self._depend_parsers:
                if parser.is_async:
                    result, errors_ = await parser.parse(*args, __depend_cache__=__depend_cache__, **kwargs)
                else:
                    result, errors_ = parser.parse(*args, __depend_cache__=__depend_cache__, **kwargs)
                if errors_:
                    errors.extend(errors_)
                data[parser.name] = result
        return data, errors


class DependsParser(ParserManager):
    def __init__(
            self,
            name: str,
            depend: Depends,
            model: Type[BaseModel],
            parent: "ParserManager",
            from_factory: "ParserManagerFactory",
            name_depend_map: Dict[str, Depends],
    ):
        self._name = name
        self._depend = depend
        self._dependency = depend.dependency
        self._parent = parent
        super().__init__(model, from_factory, name_depend_map)

    @property
    def name(self):
        return self._name

    @property
    def parent(self):
        return self._parent

    @classmethod
    def from_name_depend(
            cls,
            name: str,
            depend: Depends,
            parent: "ParserManager",
            from_factory: Optional["ParserManagerFactory"] = None
    ):
        model, name_depend_map = generate_model_from_callable(depend.dependency)
        from_factory = from_factory or parent.from_factory
        return cls(
            name=name,
            depend=depend,
            parent=parent,
            from_factory=from_factory,
            name_depend_map=name_depend_map,
            model=model,
        )

    def parse(self, *args, __depend_cache__, **kwargs):
        use_cache = self._depend.use_cache
        dependency = self._dependency
        key = dependency

        if use_cache and key in __depend_cache__:
            return __depend_cache__[key]

        data, errors = super().parse(*args, __depend_cache__=__depend_cache__, **kwargs)
        result = dependency(**data)
        if use_cache:
            __depend_cache__[key] = result
        return result, errors


class ParserManagerFactory(object):
    def __init__(
            self,
            parser_classes: Optional[Dict[str, ParserType]] = None,
            depend_parser_class: Optional[ParserType] = None
    ):
        self.parser_classes = parser_classes or {}
        self.depend_parser_class = depend_parser_class or DependsParser

    def register_parser(self, parser: ParserType) -> Callable:
        _check_parser(parser)
        params_class = parser.param_class
        name = get_name(params_class)
        self.parser_classes[name.lower()] = parser
        return parser

    def __call__(self, model: Type[BaseModel], name_depend_map) -> ParserManager:
        return ParserManager(model, self, name_depend_map)


class Parser(AsyncFlagMixin):
    is_async = False
    param_class: Type[Param]

    def __init__(self, fields: List[ModelField], manager: ParserManager):
        self.fields = fields
        self.manager = manager

    def has_parser(self) -> bool:
        return len(self.fields) != 0

    @classmethod
    def from_model(cls, model: Type[BaseModel], parser_manager: ParserManager) -> "Parser":
        fields = []
        for field in model.__fields__.values():
            if isinstance(field.field_info, cls.param_class):
                fields.append(field)

        return cls(fields, parser_manager)

    def parse(self, *args, **kwargs):
        raise NotImplemented


def single_get(obj, key) -> Any:
    return obj[key]


def multi_get(obj, key) -> Any:
    return obj.getlist(key)


class BaseMultiItemParser(Parser):
    single_get = staticmethod(single_get)
    multi_get = staticmethod(multi_get)

    def __init__(self, fields: List[ModelField], manager: ParserManager):  # noqa
        self.manager = manager
        field_getters = []
        for field in fields:
            if is_scalar_sequence_field(field):
                field_getters.append((field, self.multi_get))
            else:
                field_getters.append((field, self.single_get))
        self.field_getters = field_getters
        self.fields = fields

    def has_parser(self) -> bool:
        return len(self.field_getters) != 0
