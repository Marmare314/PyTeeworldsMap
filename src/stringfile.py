from typing import Literal


class StringFile:
    def __init__(self, path: str, mode: Literal['R', 'W']):
        self._data = b''
        self._read_mode = False
        self._pointer = 0

        if mode == 'R':
            self._read_mode = True
            with open(path, 'rb') as file:
                self._data = file.read()
        elif mode != 'W':
            raise ValueError('Unexpected mode')

    def read(self, num_bytes: int):
        if not self._read_mode:
            raise RuntimeError('File not in read mode')

        data = self._data[self._pointer:self._pointer+num_bytes]
        self._pointer += num_bytes
        return data

    def tell(self):
        return self._pointer

    def seek(self, pos: int):
        if not self._read_mode:
            raise RuntimeError('File not in read mode')

        self._pointer = pos
