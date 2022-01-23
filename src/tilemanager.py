from constants import EnumTileFlag
from typing import Optional


class Tile:
    def __init__(self, data: Optional[memoryview]):
        self._data = data


class VanillaTile(Tile):
    def __init__(self,
                 game_tile: bool,
                 type: int,
                 v_flip: bool = False,
                 h_flip: bool = False,
                 opaque: bool = False,
                 rotate: bool = False,
                 data: Optional[memoryview] = None):
        super().__init__(data)

        self._game_tile = game_tile
        self._type = type
        self.v_flip = v_flip
        self.h_flip = h_flip
        self.opaque = opaque
        self.rotate = rotate

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type: int):
        self._type = type

    @staticmethod
    def from_data(game_tile: bool, data: memoryview):
        return VanillaTile(
            game_tile,
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
    def __init__(self, width: int, height: int, data: bytes):
        self._width = width
        self._height = height
        self._data = memoryview(bytearray(data))

    def _check_coords(self, x: int, y: int):
        assert 0 <= x <= self._width
        assert 0 <= y <= self._height

    def _get_data(self, x: int, y: int, num_bits: int):
        begin = (x + y * self._width) * num_bits
        return self._data[begin:begin + num_bits]

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height


class VanillaTileManager(TileManager):
    def __init__(self, width: int, height: int, game_tiles: bool, data: bytes):
        super().__init__(width, height, data)
        self._game_tiles = game_tiles

    def get_tile(self, x: int, y: int) -> VanillaTile:
        self._check_coords(x, y)
        return VanillaTile.from_data(self._game_tiles, self._get_data(x, y, 4))


class TeleTileManager(TileManager):
    pass


class SpeedupTileManager(TileManager):
    pass


class SwitchTileManager(TileManager):
    pass


class TuneTileManager(TileManager):
    pass
