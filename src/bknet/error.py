from decimal import Decimal
from typing import NamedTuple, TypedDict, TypeVar, Union

T = TypeVar("T")
U = TypeVar("U")


### Error
class Error[T](Exception):
    data: T
    msg: str
    code: str

    def __init__(self, data: T):
        self.data = data

    def __str__(self) -> str:
        return f"{{code: {self.code}, msg: {self.msg}, data: {self.data}}}"

    def __repr__(self) -> str:
        return self.__str__()


class Success[T](NamedTuple):
    v: T
    err: None = None


class Failure[U](NamedTuple):
    v: None
    err: U


type Errorable[T, U] = Success[T] | Failure[U]


class SomethingNotEnough(TypedDict):
    action: str
    current: Union[int, float, Decimal]
    required: Union[int, float, Decimal]


class UnknownValueReceived(TypedDict):
    location: str
    value: str
