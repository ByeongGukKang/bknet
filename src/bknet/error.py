from typing import Generic, TypedDict, TypeVar

T = TypeVar("T")


### Error
class Error(Generic[T]):
    data: T
    msg: str
    code: str

    def __init__(self, data: T):
        self.data = data

    def __str__(self) -> str:
        return f"{{code: {self.code}, msg: {self.msg}, data: {self.data}}}"

    def __repr__(self) -> str:
        return self.__str__()


class SomethingNotEnough(TypedDict):
    action: str
    current: float
    required: float
