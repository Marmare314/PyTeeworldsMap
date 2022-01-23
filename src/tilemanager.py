from constants import EnumTileFlag


class Tile:
    pass


class VanillaTile(Tile):
    def __init__(self, id: int, flags: set[EnumTileFlag] = set()):
        self._id = id
        self._flags = flags


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
        self._data = data


class VanillaTileManager(TileManager):
    pass


class TeleTileManager(TileManager):
    pass


class SpeedupTileManager(TileManager):
    pass


class SwitchTileManager(TileManager):
    pass


class TuneTileManager(TileManager):
    pass
