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
        self._item_manager.clear()
        data = DataFileReader(path, self._item_manager)

        data.add_version()
        data.add_info()
        data.add_images()
        data.add_layers()
        data.add_groups()

        # asserts that a game_layer exists
        self._item_manager.game_layer

    def save(self, path: str):
        data = DataFileWriter()

        # self._item_manager.minimize_ids()  # TODO: instead -> also sort layers

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


if __name__ == '__main__':
    with open('test_maps/HeyTux2.map', 'rb') as file:
        map_content = file.read()

    m = TWMap()
    m.open(map_content)

    # print(m.info.author)
    # print(m.info.mapversion)
    # print(m.info.credits)
    # print(m.info.license)
    # print(m.info.settings)

    # saved_content = m.save('test_maps/HeyTux2Saved.map')
    # m.open(saved_content)

    # print(m.info.author)
    # print(m.info.mapversion)
    # print(m.info.credits)
    # print(m.info.license)
    # print(m.info.settings)
