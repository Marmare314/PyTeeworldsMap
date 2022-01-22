from PIL import Image
from typing import NewType, Optional

from constants import EnumTileLayerFlags

ItemReference = NewType('ItemReference', int)
ColorTuple = tuple[int, int, int, int]


# TODO: make sure references are internal and valid
class ItemManager:
    def __init__(self):
        self.version = ItemVersion(3)
        self.info = ItemInfo()
        self.images: dict[int, ItemImage] = {}
        self.envelopes: dict[int, ItemEnvelope] = {}
        self.layers: dict[int, ItemLayer] = {}
        self.groups: dict[int, ItemGroup] = {}

    def insert(self, item: 'Item'):
        pass

    def insert_with_id(self, item: 'Item', id: int):
        if isinstance(item, ItemVersion):
            self.version = item
        elif isinstance(item, ItemInfo):
            self.info = item
        elif isinstance(item, ItemImage):
            self.images[id] = item
        elif isinstance(item, ItemLayer):
            self.layers[id] = item
        elif isinstance(item, ItemGroup):
            self.groups[id] = item
        else:
            raise ValueError('type of item not known')

    def clear(self):
        pass


class Item:
    pass


class ItemVersion(Item):
    def __init__(self, version: int):
        self.version = version


class ItemInfo(Item):
    def __init__(self,
                 author: str = '',
                 mapversion: str = '',
                 credits: str = '',
                 license: str = '',
                 settings: list[str] = []):
        # TODO: write getters/setters to ensure the values can be stored

        self.author = author
        self.mapversion = mapversion
        self.credits = credits
        self.license = license
        self.settings = settings


class ItemImage(Item):
    def __init__(self):
        self._image = None
        self._name = None
        self._external = None

    def set_internal(self, image: Image.Image, name: str):
        self._image = image
        self._name = name
        self._external = False

    def set_external(self, name: str):
        # TODO: assert name is in externals
        self._image = Image.open(f'mapres/{name}.png')
        self._name = name
        self._external = True

    @property
    def image(self):
        return self._image

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        if self._external:
            raise ValueError('Cannot change name of external image')
        self._name = name


class ItemEnvelope(Item):
    pass


class ItemLayer(Item):
    def __init__(self, detail: bool = False):
        self.detail = detail


class TileLayer(ItemLayer):
    def __init__(self,
                 width: int,
                 height: int,
                 flags: list[EnumTileLayerFlags] = [],
                 color_envelope_ref: Optional[ItemEnvelope | ItemReference] = None,
                 image_ref: Optional[ItemImage | ItemReference] = None,
                 color_envelope_offset: int = 0,
                 color: ColorTuple = (0, 0, 0, 0),
                 detail: bool = False,
                 name: str = '',
                 tile_data: Optional[bytes] = None):
        pass


class QuadLayer(ItemLayer):
    pass


class SoundLayer(ItemLayer):
    pass


class ItemGroup(Item):
    def __init__(self,
                 layers: list[ItemLayer] | list[ItemReference],
                 x_offset: int = 0,
                 y_offset: int = 0,
                 x_parallax: int = 0,
                 y_parallax: int = 0,
                 clipping: bool = False,
                 clip_x: int = 0,
                 clip_y: int = 0,
                 clip_width: int = 0,
                 clip_height: int = 0,
                 name: str = ''):
        pass


class ItemSound(Item):
    pass
