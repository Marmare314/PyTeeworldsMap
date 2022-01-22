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

    def __repr__(self):
        return f'c_{"" if self._signed else "u"}int{self._num_bytes * 8}<{self._data}>'


class c_int32(c_int_impl):
    _num_bytes = 4
    _signed = True


class c_rawstr_impl(c_type):
    _length: int

    def __init__(self, data: bytes):
        assert len(data) == self._length

        self._data = data

    @property
    def value(self):
        return self._data.decode('ascii')

    @classmethod
    def from_data(cls, data: StringFile) -> 'c_rawstr_impl':
        return cls(data.read(cls._length))

    @classmethod
    def size_bytes(cls) -> int:
        return cls._length

    def __repr__(self):
        return f'c_rawstr<{self._length}, {self._data}>'


class c_rawstr4(c_rawstr_impl):
    _length = 4


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

    def __repr__(self):
        return str({var_name: getattr(self, var_name) for var_name in self.__annotations__})
