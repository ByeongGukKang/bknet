from dataclasses import dataclass
from typing import Generic, Optional, TypeAlias, TypedDict, TypeVar, Union

T = TypeVar("T")


### Error
@dataclass(slots=True, frozen=True)
class Error(Generic[T]):
    data: T
    msg: Optional[str] = ""
    code: Optional[str] = ""

    def __str__(self) -> str:
        return f"{{code: {self.code}, msg: {self.msg}, data: {self.data}}}"

    def __repr__(self) -> str:
        return self.__str__()


MaybeError: TypeAlias = Union[None, T]


class SomethingNotEnough(TypedDict):
    action: str
    current: float
    required: float
