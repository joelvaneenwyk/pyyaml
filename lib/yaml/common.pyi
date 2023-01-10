# noqa: E704

from __future__ import print_function

import builtins
import sys
import types
import unittest
from builtins import next as next
from functools import wraps as wraps
from io import BytesIO as BytesIO
from io import StringIO as StringIO

from . import moves as moves

if sys.version_info[0] == 2:
    from collections import Callable, ItemsView, Iterable
    from collections import Iterator as _Iterator
    from collections import KeysView, Mapping, ValuesView
    spec_from_loader = None
else:
    from collections.abc import Callable, ItemsView, Iterable  # type: ignore[PyUnresolvedReferences]
    from collections.abc import Iterator as _Iterator  # type: ignore[PyUnresolvedReferences]
    from collections.abc import KeysView, Mapping, ValuesView  # type: ignore[PyUnresolvedReferences]
    from importlib.util import spec_from_loader as spec_from_loader  # type: ignore[PyUnresolvedReferences]

from typing import Any, AnyStr, NoReturn, overload, Pattern, Text, TypeVar

from typing_extensions import Literal

_T = TypeVar("_T")
_K = TypeVar("_K")
_V = TypeVar("_V")

__author__: str
__version__: str

if sys.version_info < (3, 0):
    PY2: Literal[True]
    PY3: Literal[False]
    PY34: Literal[False]
    string_types: tuple[type[basestring]]  # noqa: F821
    text_type = unicode  # noqa: F821
    string_type = basestring  # noqa: F821

    def exec(
        __source: basestring,  # noqa: F821
        __globals: dict[basestring, Any] | None = ...,  # noqa: F821
        __locals: Mapping[basestring, object] | None = ...,  # noqa: F821
    ) -> None: ...
else:
    exec_ = exec
    PY2: Literal[False]
    PY3: Literal[True]
    PY34: Literal[True]
    string_types: tuple[type[str]]
    text_type = str
    string_type = str

integer_types: tuple[type[int]]
class_types: tuple[type[type]]
binary_type = bytes

MAXSIZE: int

callable = builtins.callable

def get_unbound_function(unbound: types.FunctionType) -> types.FunctionType: ...

class _C:
    def _m(self): pass
create_bound_method = type(_C()._m)

def create_unbound_method(func: types.FunctionType, cls: type) -> types.FunctionType: ...

Iterator = object

def get_method_function(meth: types.MethodType) -> types.FunctionType: ...
def get_method_self(meth: types.MethodType) -> object | None: ...
def get_function_closure(fun: types.FunctionType) -> tuple[types._Cell, ...] | None: ...
def get_function_code(fun: types.FunctionType) -> types.CodeType: ...
def get_function_defaults(fun: types.FunctionType) -> tuple[Any, ...] | None: ...
def get_function_globals(fun: types.FunctionType) -> dict[str, Any]: ...
def iterkeys(d: Mapping[_K, Any]) -> _Iterator[_K]: ...
def itervalues(d: Mapping[Any, _V]) -> _Iterator[_V]: ...
def iteritems(d: Mapping[_K, _V]) -> _Iterator[tuple[_K, _V]]: ...

# def iterlists

def viewkeys(d: Mapping[_K, Any]) -> KeysView[_K]: ...
def viewvalues(d: Mapping[Any, _V]) -> ValuesView[_V]: ...
def viewitems(d: Mapping[_K, _V]) -> ItemsView[_K, _V]: ...
def b(s: Text) -> bytes: ...
def u(s: Text) -> text_type: ...

unichr = chr

def int2byte(i: int) -> bytes: ...
def byte2int(bs: bytes) -> int: ...
def indexbytes(buf: bytes, i: int) -> int: ...
def iterbytes(buf: bytes) -> _Iterator[int]: ...
def assertCountEqual(self: unittest.TestCase, first: Iterable[_T], second: Iterable[_T], msg: str | None = ...) -> None: ...
@overload
def assertRaisesRegex(self: unittest.TestCase, msg: str | None = ...) -> Any: ...
@overload
def assertRaisesRegex(self: unittest.TestCase, callable_obj: Callable[..., Any], *args: Any, **kwargs: Any) -> Any: ...
def assertRegex(
    self: unittest.TestCase, text: AnyStr, expected_regex: AnyStr | Pattern[AnyStr], msg: str | None = ...
) -> None: ...

def reraise(tp: type[BaseException] | None, value: BaseException | None, tb: types.TracebackType | None = ...) -> NoReturn: ...
def raise_from(value: BaseException | type[BaseException], from_value: BaseException | None) -> NoReturn: ...

print_ = print

def with_metaclass(meta: type, *bases: type) -> type: ...
def add_metaclass(metaclass: type) -> Callable[[_T], _T]: ...
def ensure_binary(s: bytes | string_type, encoding: str = ..., errors: str = ...) -> bytes: ...
def ensure_str(s: bytes | string_type, encoding: str = ..., errors: str = ...) -> str: ...
def ensure_text(s: bytes | string_type, encoding: str = ..., errors: str = ...) -> Text: ...
def python_2_unicode_compatible(klass: _T) -> _T: ...

class _LazyDescr:
    name: str
    def __init__(self, name: str) -> None: ...
    def __get__(self, obj: object | None, tp: object) -> Any: ...

class MovedModule(_LazyDescr):
    mod: str
    def __init__(self, name: str, old: str, new: str | None = ...) -> None: ...
    def __getattr__(self, attr: str) -> Any: ...

class MovedAttribute(_LazyDescr):
    mod: str
    attr: str
    def __init__(self, name: str, old_mod: str, new_mod: str, old_attr: str | None = ..., new_attr: str | None = ...) -> None: ...

def add_move(move: MovedModule | MovedAttribute) -> None: ...
def remove_move(name: str) -> None: ...
