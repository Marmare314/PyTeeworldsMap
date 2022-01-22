from DataFileReader import DataFileReader
from utils import ItemType


class TileManager:
    def __init__(self, width: int, height: int, data: bytes):
        self.width = width
        self.height = height
        self._data = data

    @staticmethod
    def from_data_any(data: DataFileReader, index: int):
        layer_data = data.get_item(ItemType.LAYER, index)
        flags = layer_data['data']['flags']
        width, height = layer_data['data']['width'], layer_data['data']['height']

        if flags == 0 or flags == 1 or flags == 8:
            return VanillaTileManager(width, height, data.get_data(layer_data['data']['data_ptr']))
        elif flags == 2:
            return TeleTileManager(width, height, data.get_data(layer_data['data']['data_tele_ptr']))
        elif flags == 4:
            return SpeedupTileManager(width, height, data.get_data(layer_data['data']['data_speedup_ptr']))
        elif flags == 16:
            return SwitchTileManager(width, height, data.get_data(layer_data['data']['data_switch_ptr']))
        elif flags == 32:
            return TuneTileManager(width, height, data.get_data(layer_data['data']['data_tune_ptr']))


class VanillaTileManager(TileManager):
    def __init__(self, width: int, height: int, data: bytes):
        super().__init__(width, height, data)


class TeleTileManager(TileManager):
    def __init__(self, width: int, height: int, data: bytes):
        super().__init__(width, height, data)


class SpeedupTileManager(TileManager):
    def __init__(self, width: int, height: int, data: bytes):
        super().__init__(width, height, data)


class SwitchTileManager(TileManager):
    def __init__(self, width: int, height: int, data: bytes):
        super().__init__(width, height, data)


class TuneTileManager(TileManager):
    def __init__(self, width: int, height: int, data: bytes):
        super().__init__(width, height, data)
