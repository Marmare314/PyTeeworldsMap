from Items import ItemEnvelope, ItemGroup, ItemImage, ItemInfo, ItemVersion, TileLayer
from DataFileReader import DataFileReader


class Map:
    def __init__(self):
        self.version = ItemVersion(id=0, version=1)
        self.info = ItemInfo(id=0)
        self.images: list[ItemImage] = []
        self.envelopes: list[ItemEnvelope] = []
        self.groups: list[ItemGroup] = []

        # TODO: init id counters

    @property
    def game_layer(self):
        for group in self.groups:
            for layer in group.layers:
                if isinstance(layer, TileLayer):
                    if layer.flags == 0:
                        return layer

    @staticmethod
    def from_file(path: str):
        data = DataFileReader(path)

        new_map = Map()

        new_map.version = ItemVersion.from_data(data)
        new_map.info = ItemInfo.from_data(data)
        new_map.images = ItemImage.from_data_all(data)
        new_map.envelopes = ItemEnvelope.from_data_all(data)
        new_map.groups = ItemGroup.from_data_all(data)

        return new_map


if __name__ == '__main__':
    m = Map.from_file('HeyTux2.map')
    print(m.game_layer.tiles)
