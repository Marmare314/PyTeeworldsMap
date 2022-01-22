from datafile_reader import DataFileReader
from items import ItemManager


class TWMap:
    def __init__(self):
        self._item_manager = ItemManager()

    def open(self, path: str):
        data = DataFileReader(path)

        self._item_manager.clear()

        self._item_manager.insert_with_id(*data.item_version)
        self._item_manager.insert_with_id(*data.item_info)

        for image, i in data.item_images:
            self._item_manager.insert_with_id(image, i)

        for layer, i in data.item_layers:
            self._item_manager.insert_with_id(layer, i)

        for group, i in data.item_groups:
            self._item_manager.insert_with_id(group, i)

    @property
    def game_layer(self):
        return self._item_manager.game_layer


m = TWMap()
m.open('test_maps/HeyTux2.map')
m.game_layer.get_tile(0, 0)
