from typing import Type, TypeVar, List

from pytwmap.stringfile import StringFile


T = TypeVar('T')
TCTYPE = TypeVar('TCTYPE', bound='c_type')


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
    def from_data(cls: Type[T], data: StringFile) -> T:
        raise NotImplementedError()

    # TODO: make this take stringfile too?
    def to_data(self) -> bytes:
        raise NotImplementedError()

    @classmethod
    def size_bytes(cls) -> int:
        raise NotImplementedError()


class c_int_impl(c_type, int):
    _num_bytes: int
    _signed: bool

    def __new__(cls, value: int):
        assert cls.fits_value(value)
        return super(c_int_impl, cls).__new__(cls, value)

    @classmethod
    def fits_value(cls, value: int):
        if cls._signed:
            limit = 2 ** (cls._num_bytes * 8 - 1)
            return -limit <= value < limit
        else:
            return 0 <= value < 2 ** (cls._num_bytes * 8)

    @classmethod
    def from_data(cls, data: StringFile) -> 'c_int_impl':
        return cls(int.from_bytes(data.read(cls._num_bytes), byteorder='little', signed=cls._signed))

    def to_data(self):
        return self.to_bytes(self._num_bytes, byteorder='little', signed=self._signed)

    @classmethod
    def size_bytes(cls) -> int:
        return cls._num_bytes


class c_int32(c_int_impl):
    _num_bytes = 4
    _signed = True


class c_str_impl(c_type, str):
    _length: int

    def __new__(cls, value: str):
        assert cls.fits_str(value)
        return super(c_str_impl, cls).__new__(cls, value)

    @classmethod
    def fits_str(cls, value: str):
        return len(cls._encode(value)) == cls._length

    @classmethod
    def _encode(cls, msg: str) -> bytes:
        raise NotImplementedError()

    @classmethod
    def _decode(cls, msg: bytes) -> str:
        raise NotImplementedError()

    @classmethod
    def from_data(cls, data: StringFile) -> 'c_str_impl':
        return cls(cls._decode(data.read(cls._length)))

    def to_data(self):
        return self._encode(self)

    @classmethod
    def size_bytes(cls) -> int:
        return cls._length


class c_rawstr4(c_str_impl):
    _length = 4

    @classmethod
    def _encode(cls, msg: str):
        return msg.encode('utf8')

    @classmethod
    def _decode(cls, msg: bytes):
        return msg.decode('utf8')


class c_intstr_impl(c_str_impl):
    @classmethod
    def _encode(cls, msg: str):
        byte_msg = b''
        msg = msg.ljust(cls._length, '\0')
        for i in range(0, len(msg), 4):
            for b in msg[i:i+4][::-1]:
                byte_msg += bytes([safe_ord(b) + 128])
        return byte_msg

    @classmethod
    def _decode(cls, msg: bytes):
        str_msg = ''
        for i in range(0, len(msg), 4):
            for b in msg[i:i+4][::-1]:
                str_msg += safe_chr(b - 128)

        return str_msg[:-1].rstrip('\0')


class c_intstr3(c_intstr_impl):
    _length = 3 * c_int32.size_bytes()


class c_intstr8(c_intstr_impl):
    _length = 8 * c_int32.size_bytes()


class c_struct(c_type):
    @classmethod
    def from_data(cls: Type[T], data: StringFile) -> 'T':
        instance = cls()
        for var_name in cls.__annotations__:
            attr_type = cls.__annotations__[var_name]
            setattr(instance, var_name, attr_type.from_data(data))

        return instance

    def to_data(self):
        ret = b''
        for var_name in self.__annotations__:
            ret += getattr(self, var_name).to_data()
        return ret

    @classmethod
    def size_bytes(cls) -> int:
        size = 0
        for var_name in cls.__annotations__:
            size += cls.__annotations__[var_name].size_bytes()
        return size


class c_int32_color(c_struct):
    r: c_int32
    g: c_int32
    b: c_int32
    a: c_int32

    @staticmethod
    def from_values(r: int, g: int, b: int, a: int):
        col = c_int32_color()
        col.r = c_int32(r)
        col.g = c_int32(g)
        col.b = c_int32(b)
        col.a = c_int32(a)
        return col

    def as_tuple(self):
        return self.r, self.g, self.b, self.a


class c_int32_point(c_struct):
    x: c_int32
    y: c_int32

    @staticmethod
    def from_values(x: int, y: int):
        p = c_int32_point()
        p.x = c_int32(x)
        p.y = c_int32(y)
        return p

    def as_tuple(self):
        return self.x, self.y


class c_array_impl(c_type, List[TCTYPE]):
    _length: int
    _type: Type[TCTYPE]

    def __init__(self, value: 'list[TCTYPE]'):
        super().__init__(value)

        assert len(value) == self._length

    @classmethod
    def from_data(cls, data: StringFile) -> 'c_array_impl[TCTYPE]':
        return cls([cls._type.from_data(data) for _ in range(cls._length)])

    def to_data(self):
        b = b''
        for x in self:
            b += x.to_data()
        return b


class c_point_array5(c_array_impl[c_int32_point]):
    _length = 5
    _type = c_int32_point


class c_point_array4(c_array_impl[c_int32_point]):
    _length = 4
    _type = c_int32_point


class c_color_array4(c_array_impl[c_int32_color]):
    _length = 4
    _type = c_int32_color
