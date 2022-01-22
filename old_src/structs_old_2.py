from typing import ClassVar, Type, TypeVar, Generic, Literal
from stringfile import StringFile


class c_type:
    @staticmethod
    def read(cls_type: 'Type[c_type]', data: StringFile) -> 'c_type':
        raise NotImplementedError()

    @property
    def size_bytes(self) -> int:
        return 0


class c_char(c_type):
    def __init__(self, data: bytes):
        assert len(data) == 1
        pass

    @staticmethod
    def read(cls_type: 'Type[c_type]', data: StringFile) -> 'c_char':
        assert cls_type == c_char

        return c_char(data.read(1))

    @property
    def size_bytes(self) -> int:
        return 1


T = TypeVar('T', bound=c_type)
SIZE = TypeVar('SIZE', bound=int)


class c_array(Generic[T, SIZE], c_type):
    abc: ClassVar[str] = SIZE.__dict__

    def __init__(self, data: list[T]):
        pass

    @staticmethod
    def read(cls_type: 'Type[c_type]', data: StringFile) -> 'c_array[T, SIZE]':
        assert cls_type.__origin__ == c_array  # type: ignore

        t: Type[c_type]
        size: SIZE
        t, size = cls_type.__args__  # type: ignore
        size_int: int = size.__args__[0]  # type: ignore

        t.read(t, data)
        return c_array[T, SIZE]([t.read(c_char, data) for _ in range(size_int)])

    # @property
    # def size_bytes(self) -> int:
    #     return len(self) * 

    # def __len__(self):
    #     return self._length

    @classmethod
    def test(cls):
        print(cls.abc)


class MyType:
    def __getitem__(self, t: type):
        return T

M = MyType()
x: M[int] = 3


s = StringFile('test_maps/HeyTux2.map', 'R')
# c_array[c_char, Literal[2]].read(c_array[c_char, Literal[2]], s)
c_array[c_char, Literal[2]].test()

# class c_array_impl(c_type):
#     _length: ClassVar[int]
#     _type: Type[c_type]

#     def __init__(self, data: list[_type]):
#         assert len(data) == self._length

#         self._data = data

#     @classmethod
#     def from_data(cls, data: StringFile) -> c_array_impl:
#         return cls([cls._type.from_data(data) for _ in range(cls._length)])

#     @classmethod
#     def size_bytes(cls) -> int:
#         return cls._length * cls._type.size_bytes()

#     def __repr__(self):
#         return f'{self._data}'


# class c_array_char_4(c_array_impl):
#     _length = 4
#     _type = c_char
