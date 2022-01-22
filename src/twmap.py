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


m = TWMap()
m.open('test_maps/HeyTux2.map')
