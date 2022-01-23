from datafile_reader import DataFileReader
from items import ItemManager


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
            self._item_manager.add(layer)

        for group in data.item_groups:
            self._item_manager.add(group)

    @property
    def info(self):
        return self._item_manager.info

    # @property
    # def groups(self):
    #     # TODO: can items be modified through this?
    #     return list(self._item_manager.groups.values())

    @property
    def game_layer(self):
        return self._item_manager.game_layer


m = TWMap()
m.open('test_maps/HeyTux2.map')
print(m.info)
