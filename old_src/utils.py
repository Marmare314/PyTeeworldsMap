from __future__ import annotations


def int32(x: int):
    if x > 0xFFFFFFFF:
        raise OverflowError
    if x > 0x7FFFFFFF:
        x = int(0x100000000-x)
        if x < 2147483648:
            return -x
        else:
            return -2147483648
    return x


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


def string_to_ints(in_string: str, length: int = 8):
    ints: list[int] = []
    for i in range(length):
        string = ''
        for j in range(i*4, i*4+4):
            if in_string and j < len(in_string):
                string += in_string[j]
            else:
                string += chr(0)
        ints.append(int32(((safe_ord(string[0])+128) << 24) | ((safe_ord(string[1])+128) << 16) | (
            (safe_ord(string[2])+128) << 8) | (safe_ord(string[3])+128)))
    ints[-1] &= int32(0xffffff00)
    return ints


def ints_to_string(num: list[int]):
    return ''.join([''.join([
        safe_chr(((val >> 24) & 0xff)-128),
        safe_chr(((val >> 16) & 0xff)-128),
        safe_chr(((val >> 8) & 0xff)-128),
        safe_chr((val & 0xff)-128),
    ]) for val in num]).partition('\x00')[0]
