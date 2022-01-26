class StringFile:
    def __init__(self, data: bytes):
        self._data = data
        self._pointer = 0

    def read(self, num_bytes: int):
        data = self._data[self._pointer:self._pointer+num_bytes]
        self._pointer += num_bytes
        return data

    def read_all(self):
        return self._data

    def tell(self):
        return self._pointer

    def seek(self, pos: int):
        self._pointer = pos

    def append(self, data: bytes):
        self._data += data
        self._pointer = len(data)

    def __len__(self):
        return len(self._data)
