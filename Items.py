from __future__ import annotations

from PIL import Image
from DataFileReader import DataFileReader
from utils import ItemType
from TileManager import TileManager


class Item:
    def __init__(self, id: int):
        self._id = id


class ItemVersion(Item):
    def __init__(self, id: int, version: int):
        super().__init__(id)

        self.version = version

    @staticmethod
    def from_data(data: DataFileReader):
        version_data = data.get_item(ItemType.VERSION, 0)
        return ItemVersion(0, version_data['version'])


class ItemInfo(Item):
    def __init__(self, id: int, author: str = '', mapversion: str = '', credits: str = '', license: str = '', settings: list[str] = []):
        super().__init__(id)

        self.author = author
        self.mapversion = mapversion
        self.credits = credits
        self.license = license
        self.settings = settings

    @staticmethod
    def from_data(data: DataFileReader):
        pass


class ItemImage(Item):
    def __init__(self, id: int, image: Image.Image, name: int, external: bool):
        super().__init__(id)

        self.image = image
        self.name = name
        self.external = external

    @staticmethod
    def from_data(data: DataFileReader, index: int):
        image_data = data.get_item(ItemType.IMAGE, index)

        name = data.get_data_str(image_data['name_ptr'])
        if image_data['external']:
            image = Image.open(f'mapres/{name}.png')
            return ItemImage(index, image, name, True)
        else:
            image = Image.frombytes('RGBA', (image_data['width'], image_data['height']), data.get_data(image_data['data_ptr']))
            return ItemImage(index, image, name, False)

    @staticmethod
    def from_data_all(data: DataFileReader):
        return [ItemImage.from_data(data, i) for i in range(data.get_num_items(ItemType.IMAGE))]


class ItemEnvelope(Item):
    @staticmethod
    def from_data(data: DataFileReader, index: int):
        return []

    @staticmethod
    def from_data_all(data: DataFileReader):
        return []


class ItemLayer(Item):
    def __init__(self, id: int, layer_flags: int):
        super().__init__(id)

        self.layer_flags = layer_flags

    @staticmethod
    def from_data_any(data: DataFileReader, index: int):
        layer_data = data.get_item(ItemType.LAYER, index)
        if layer_data['type'] == 2:
            return TileLayer.from_item_data(data, index)
        elif layer_data['type'] == 3:
            return QuadLayer.from_item_data(data, index)
        elif layer_data['type'] == 9 or layer_data['type'] == 10:
            return SoundLayer.from_item_data(data, index)


class TileLayer(ItemLayer):
    def __init__(self, id: int, layer_flags: int, flags: int, color: list[int], color_envelope_offset: int, name: str, tiles: TileManager):
        super().__init__(id, layer_flags)

        self.flags = flags
        self.color = color
        self.color_envelope_offset = color_envelope_offset
        self.name = name
        self.tiles = tiles

    @staticmethod
    def from_item_data(data: DataFileReader, index: int):
        # TODO: what to do with color_envelope_ref, image_ref
        layer_data = data.get_item(ItemType.LAYER, index)

        return TileLayer(
            index,
            layer_data['flags'],
            layer_data['data']['flags'],
            layer_data['data']['color'],
            layer_data['data']['color_envelope_offset'],
            layer_data['data']['name'],
            TileManager.from_data_any(data, index)
        )


class QuadLayer(ItemLayer):
    def __init__(self, id: int, layer_flags: int):
        pass

    @staticmethod
    def from_item_data(data: DataFileReader, index: int):
        pass


class SoundSource(Item):
    pass


class SoundLayer(ItemLayer):
    def __init__(self, id: int, layer_flags: int):
        pass

    @staticmethod
    def from_item_data(data: DataFileReader, index: int):
        pass


class ItemGroup(Item):
    def __init__(self, id: int, x_offset: int, y_offset: int, x_parallax: int, y_parallax: int, layers: list[ItemLayer], clipping: bool, clip_x: int, clip_y: int, clip_width: int, clip_height: int, name: str):
        super().__init__(id)

        self.x_offset = x_offset
        self.y_offset = y_offset
        self.x_parallax = x_parallax
        self.y_parallax = y_parallax
        self.layers = layers
        self.clipping = clipping
        self.clip_x = clip_x
        self.clip_y = clip_y
        self.clip_width = clip_width
        self.clip_height = clip_height
        self.name = name

    @staticmethod
    def from_data(data: DataFileReader, index: int):
        group_data = data.get_item(ItemType.GROUP, index)

        layers: list[ItemLayer] = []
        for i in range(group_data['num_layers']):
            layers.append(ItemLayer.from_data_any(data, group_data['start_layer'] + i))

        return ItemGroup(
            index,
            group_data['x_offset'],
            group_data['y_offset'],
            group_data['x_parallax'],
            group_data['y_parallax'],
            layers,
            group_data['clipping'],
            group_data['clip_x'],
            group_data['clip_y'],
            group_data['clip_width'],
            group_data['clip_height'],
            group_data['name']
        )

    @staticmethod
    def from_data_all(data: DataFileReader):
        return [ItemGroup.from_data(data, i) for i in range(data.get_num_items(ItemType.GROUP))]
