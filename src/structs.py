from typing import Type, TypeVar
from stringfile import StringFile


class c_type:
    @classmethod
    def from_data(cls, data: StringFile) -> 'c_type':
        raise NotImplementedError()

    @classmethod
    def size_bytes(cls) -> int:
        raise NotImplementedError()


class c_int_impl(c_type):
    _num_bytes: int
    _signed: bool

    def __init__(self, data: int):
        # TODO: assert range
        self._data = data

    @property
    def value(self):
        return self._data

    @classmethod
    def from_data(cls, data: StringFile) -> 'c_int_impl':
        return cls(int.from_bytes(data.read(cls._num_bytes), byteorder='little', signed=cls._signed))

    @classmethod
    def size_bytes(cls) -> int:
        return cls._num_bytes


class c_int32(c_int_impl):
    _num_bytes = 4
    _signed = True


class c_uint16(c_int_impl):
    _num_bytes = 2
    _signed = False


class c_str_impl(c_type):
    _length: int

    def __init__(self, data: bytes):
        assert len(data) == self._length

        self._data = data

    @classmethod
    def from_data(cls, data: StringFile) -> 'c_str_impl':
        return cls(data.read(cls._length))

    @classmethod
    def size_bytes(cls) -> int:
        return cls._length


class c_rawstr4(c_str_impl):
    _length = 4

    @property
    def value(self):
        return self._data.decode('utf8')


class c_intstr3(c_str_impl):
    _length = 4

    @property
    def value(self):


T = TypeVar('T')


class c_struct:
    @classmethod
    def from_data(cls: Type[T], data: StringFile) -> 'T':
        instance = cls()
        for var_name in cls.__annotations__:
            attr_type = cls.__annotations__[var_name]
            setattr(instance, var_name, attr_type.from_data(data))

        return instance

    @classmethod
    def size_bytes(cls) -> int:
        size = 0
        for var_name in cls.__annotations__:
            size += cls.__annotations__[var_name].size_bytes()
        return size


class c_i32_color(c_struct):
    r: c_int32
    g: c_int32
    b: c_int32
    a: c_int32
