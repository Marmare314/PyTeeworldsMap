from constants import EnumTileFlag, EnumTileType
from typing import Optional


class TileManager:
    _tile_bytes: int

    def __init__(self, width: int, height: int, data: Optional[bytes] = None):
        needed_bytes = width * height * self._tile_bytes
        if data is None:
            self._data = bytearray(needed_bytes)
        else:
            self._data = bytearray(data)
        assert len(self._data) == needed_bytes
        self._width = width
        self._height = height

    def _check_coords(self, x: int, y: int):
        assert 0 <= x <= self._width
        assert 0 <= y <= self._height

    def _set_field(self, x: int, y: int, num_byte: int, value: int):
        self._check_coords(x, y)
        assert 0 <= num_byte < self._tile_bytes
        assert 0 <= value < 256

        begin = (x + y * self._width) * self._tile_bytes
        self._data[begin+num_byte] = value

    def _get_field(self, x: int, y: int, num_byte: int):
        self._check_coords(x, y)
        assert 0 <= num_byte < self._tile_bytes

        begin = (x + y * self._width) * self._tile_bytes
        return self._data[begin+num_byte]

    def get_id(self, x: int, y: int) -> int:
        raise NotImplementedError()

    def set_id(self, x: int, y: int, value: int) -> None:
        raise NotImplementedError()

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def raw_data(self):
        return self._data


class VanillaTileManager(TileManager):
    _tile_bytes = 4

    def get_id(self, x: int, y: int):
        return self._get_field(x, y, 0)

    def set_id(self, x: int, y: int, value: int | EnumTileType):
        return self._set_field(x, y, 0, value)

    def has_flag(self, x: int, y: int, f: EnumTileFlag):
        return f & self._get_field(x, y, 1) > 0


class TeleTileManager(TileManager):
    _tile_bytes = 2

    def get_id(self, x: int, y: int) -> int:
        return self._get_field(x, y, 1)


class SpeedupTileManager(TileManager):
    _tile_bytes = 6

    def get_id(self, x: int, y: int) -> int:
        return self._get_field(x, y, 1)


class SwitchTileManager(TileManager):
    _tile_bytes = 4

    def get_id(self, x: int, y: int) -> int:
        return self._get_field(x, y, 1)


class TuneTileManager(TileManager):
    _tile_bytes = 2

    def get_id(self, x: int, y: int) -> int:
        return self._get_field(x, y, 1)
