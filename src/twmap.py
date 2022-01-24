# pyright: reportPrivateUsage=false

from datafile_reader import DataFileReader
from datafile_writer import DataFileWriter
from items import ItemManager, VanillaTileLayer


class TWMap:
    def __init__(self):
        self._item_manager = ItemManager()

    def open(self, path: bytes):
        # with open(path, 'rb') as file:
        #     data = DataFileReader(file.read())
        data = DataFileReader(path)

        self._item_manager.clear()

        self._item_manager.add(data.item_version)
        self._item_manager.add(data.item_info)

        for image in data.item_images:
            self._item_manager.add(image)

        # for layer in data.item_layers:
        #     layer._set_references_import(self._item_manager)
        #     self._item_manager.add(layer)

        # for group in data.item_groups:
        #     group._set_references_import(self._item_manager)
        #     self._item_manager.add(group)

        # # asserts that a game_layer exists
        # self._item_manager.game_layer

    def save(self, path: str):
        data = DataFileWriter()

        self._item_manager.minimize_ids()

        data.register_item(self._item_manager.version)
        data.register_item(self._item_manager.info)

        for image in self._item_manager.images:
            data.register_item(image)

        return data.write(path)

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


with open('test_maps/testmap.map', 'rb') as file:
    map_content = file.read()

m = TWMap()
m.open(map_content)

print(m.info.author)
print(m.info.mapversion)
print(m.info.credits)
print(m.info.license)
print(m.info.settings)

saved_content = m.save('test_maps/HeyTux2Saved.map')

m.open(saved_content)

print(m.info.author)
print(m.info.mapversion)
print(m.info.credits)
print(m.info.license)
print(m.info.settings)
