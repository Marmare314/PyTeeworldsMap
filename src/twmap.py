# pyright: reportPrivateUsage=false

from datafile_reader import DataFileReader
from datafile_writer import DataFileWriter
from items import ItemManager, VanillaTileLayer


# TODO: make exceptions/asserts consistent
# TODO: try to remove type ignores


class TWMap:
    def __init__(self):
        self._item_manager = ItemManager()

    def open(self, path: str):
        self._item_manager.clear()

        with open(path, 'rb') as file:
            data = DataFileReader(file.read(), self._item_manager)

        data.add_version()
        data.add_info()
        data.add_images()
        data.add_layers()
        data.add_groups()

        # asserts that a game_layer exists
        self._item_manager.game_layer

    def save(self, path: str):
        data = DataFileWriter()

        self._item_manager.clean_ids()

        data.register_item(self._item_manager.version)
        data.register_item(self._item_manager.info)

        for image in self._item_manager.images:
            data.register_item(image)

        for layer in self._item_manager.layers:
            data.register_item(layer)

        for group in self._item_manager.groups:
            data.register_item(group)

        return data.write(path)

    @property
    def info(self):
        return self._item_manager.info

    @property
    def images(self):
        return list(self._item_manager.images)

    @property
    def layers(self):
        return list(self._item_manager.layers)

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
    m = TWMap()
    m.open('../test_maps/XmasMove.map')
    # m.save('../test_maps/XmasMoveSaved.map')
    m.save('/home/marek/.teeworlds/maps/XmasMoveSaved.map')
