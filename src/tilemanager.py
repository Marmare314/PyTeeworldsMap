from constants import EnumTileFlag, EnumTileType
from typing import Optional


class Tile:
    def __init__(self, data: Optional[memoryview]):
        self._data = data

    def _set_byte(self, num_byte: int, value: int):
        # TODO: check inputs
        if self._data is not None:
            self._data[num_byte] = value


class VanillaTile(Tile):
    def __init__(self,
                 type: int,
                 v_flip: bool = False,
                 h_flip: bool = False,
                 opaque: bool = False,
                 rotate: bool = False,
                 data: Optional[memoryview] = None):
        super().__init__(data)

        self._type = type
        self._v_flip = v_flip
        self._h_flip = h_flip
        self._opaque = opaque
        self._rotate = rotate

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type: int | EnumTileType):
        self._set_byte(0, type)
        self._type = type

    @staticmethod
    def from_data(data: memoryview):
        assert len(data) == 4
        return VanillaTile(
            data[0],
            EnumTileFlag.VFLIP & data[1] > 0,
            EnumTileFlag.HFLIP & data[1] > 0,
            EnumTileFlag.OPAQUE & data[1] > 0,
            EnumTileFlag.ROTATE & data[1] > 0,
            data
        )


class TeleTile(Tile):
    pass


class SpeedupTile(Tile):
    pass


class SwitchTile(Tile):
    pass


class TuneTile(Tile):
    pass


class TileManager:
    _tile_bytes: int

    def __init__(self, width: int, height: int, data: Optional[bytes] = None):
        needed_bytes = width * height * self._tile_bytes
        if data is None:
            self._data = memoryview(bytearray(needed_bytes))
        else:
            self._data = memoryview(bytearray(data))
        assert len(self._data) == needed_bytes
        self._width = width
        self._height = height

    def _check_coords(self, x: int, y: int):
        assert 0 <= x <= self._width
        assert 0 <= y <= self._height

    def _get_data(self, x: int, y: int):
        self._check_coords(x, y)
        begin = (x + y * self._width) * self._tile_bytes
        return self._data[begin:begin+self._tile_bytes]

    def get_tilebyte(self, x: int, y: int, num_byte: int):
        self._check_coords(x, y)
        assert 0 <= num_byte < self._tile_bytes
        begin = (x + y * self._width) * self._tile_bytes
        return self._data[begin+num_byte]

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

    def get_tile(self, x: int, y: int) -> VanillaTile:
        self._check_coords(x, y)
        return VanillaTile.from_data(self._get_data(x, y))


class TeleTileManager(TileManager):
    _tile_bytes = 2


class SpeedupTileManager(TileManager):
    _tile_bytes = 6


class SwitchTileManager(TileManager):
    _tile_bytes = 4


class TuneTileManager(TileManager):
    _tile_bytes = 2
