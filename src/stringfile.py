class StringFile:
    def __init__(self, data: bytes):
        self._data = data
        self._pointer = 0

    def read(self, num_bytes: int):
        data = self._data[self._pointer:self._pointer+num_bytes]
        self._pointer += num_bytes
        return data

    def tell(self):
        return self._pointer

    def seek(self, pos: int):
        self._pointer = pos
