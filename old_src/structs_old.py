from typing import Any, Generic, TypeVar, Type, Literal
from stringfile import StringFile


class BasicType:
    _required_bytes = 0

    def __init__(self, data: bytes):
        self._data = data

    @staticmethod
    def read(cls_type: 'Type[BasicType]', data: StringFile):
        return cls_type(data.read(cls_type._required_bytes))

    @property
    def data(self) -> Any:
        raise NotImplementedError()

    @property
    @classmethod
    def size(cls) -> int:
        return cls._required_bytes


class c_char(BasicType):
    _required_bytes = 1

    @property
    def data(self) -> bytes:
        return self._data


class c_int32(BasicType):
    _required_bytes = 4

    @property
    def data(self) -> int:
        return 1


T = TypeVar('T', bound=BasicType)
SIZE = TypeVar('SIZE', bound=int)


class test:
    def __init__(self, f):
        self._f = f

    def __call__(self, *args, **kwargs):
        print(args, kwargs)


class Array(Generic[T, SIZE], BasicType):
    @test
    def read(cls, data: StringFile):
        t: BasicType
        size: SIZE
        t, size = cls_type.__args__  # type: ignore
        size_int: int = size.__args__[0]  # type: ignore

        return Array[T, SIZE](data.read(t.size * size_int))

    @property
    def data(self) -> list[T]:
        return []

    @property
    @classmethod
    def size(cls) -> int:
        return cls._required_bytes


class RawString(Generic[SIZE]):
    pass


class IntegerString(Generic[SIZE]):
    pass


class Struct:
    @classmethod
    def read(cls, data: StringFile):
        instance = cls()
        for var_name in cls.__annotations__:
            attr_type = cls.__annotations__[var_name]
            attr_type.read(attr_type, data)

        return instance


class VersionHeader(Struct):
    _magic: Array[c_char, Literal[4]]

    # @property
    # def magic(self):
    #     return self._magic[0].data


s = StringFile('test_maps/HeyTux2.map', 'R')
t = VersionHeader.read(s)
# print(Array[c_char, Literal[4]])
# Array[c_char, Literal[4]].read(s)
# print(t.magic)

# print(tuple[c_char].__class__)
