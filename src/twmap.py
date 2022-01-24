# pyright: reportPrivateUsage=false

from datafile_reader import DataFileReader
from items import ItemManager, VanillaTileLayer


class TWMap:
    def __init__(self):
        self._item_manager = ItemManager()

    def open(self, path: str):
        data = DataFileReader(path)

        self._item_manager.clear()

        self._item_manager.add(data.item_version)
        self._item_manager.add(data.item_info)

        for image in data.item_images:
            self._item_manager.add(image)

        for layer in data.item_layers:
            layer._set_references_import(self._item_manager)
            self._item_manager.add(layer)

        for group in data.item_groups:
            group._set_references_import(self._item_manager)
            self._item_manager.add(group)

        # asserts that a game_layer exists
        self._item_manager.game_layer

    @property
    def info(self):
        return self._item_manager.info

    @property
    def groups(self):
        return list(self._item_manager.groups)

    @property
    def game_layer(self):
        return self._item_manager.game_layer

    @game_layer.setter
    def game_layer(self, layer: VanillaTileLayer):
        pass


m = TWMap()
m.open('test_maps/HeyTux2.map')
