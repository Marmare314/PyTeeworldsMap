from typing import Type, TypeVar
from stringfile import StringFile


def safe_ord(char: str):
    num = ord(char)
    if num > 0x7F:
        num = 0x100 - num
        if num < 128:
            return -num
        else:
            return -128
    return num


def safe_chr(i: int):
    return chr(max(0, min(i if i >= 0 else 256 + i, 256)))


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

    def __init__(self, value: int):
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value: int):
        # TODO: check range
        self._value = value

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

    def __init__(self, value: str):
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value: str):
        assert len(self._encode(value)) == self._length

        self._value = value

    @staticmethod
    def _encode(msg: str) -> bytes:
        raise NotImplementedError()

    @staticmethod
    def _decode(msg: bytes) -> str:
        raise NotImplementedError()

    @classmethod
    def from_data(cls, data: StringFile) -> 'c_str_impl':
        return cls(cls._decode(data.read(cls._length)))

    @classmethod
    def size_bytes(cls) -> int:
        return cls._length


class c_rawstr4(c_str_impl):
    _length = 4

    @staticmethod
    def _encode(msg: str):
        return msg.encode('utf8')

    @staticmethod
    def _decode(msg: bytes):
        return msg.decode('utf8')


class c_intstr_impl(c_str_impl):
    @staticmethod
    def _encode(msg: str):
        byte_msg = b''
        for i in range(0, len(msg), 4):
            for b in msg[i:i+4][::-1]:
                byte_msg += bytes([safe_ord(b) + 128])
        return byte_msg

    @staticmethod
    def _decode(msg: bytes):
        str_msg = ''
        for i in range(0, len(msg), 4):
            for b in msg[i:i+4][::-1]:
                str_msg += safe_chr(b - 128)

        return str_msg

class c_intstr3(c_intstr_impl):
    _length = 12  # 3 * c_int32


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

    @property
    def value(self):
        return self.r.value, self.g.value, self.b.value, self.a.value
