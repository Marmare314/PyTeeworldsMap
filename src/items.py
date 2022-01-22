from PIL import Image
from typing import Optional, Type

from constants import EnumTileLayerFlags
from structs import c_intstr3
from map_structs import CTileVanilla
from stringfile import StringFile

ColorTuple = tuple[int, int, int, int]


# TODO: make sure references are internal and valid
class ItemManager:
    def __init__(self):
        # TODO: insert game layer on init

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
        self.images = {}
        self.envelopes = {}
        self.layers = {}
        self.groups = {}

    @property
    def game_layer(self) -> 'TileLayer':
        for layer_id in self.layers:
            if self.layers[layer_id].game_layer:
                layer = self.layers[layer_id]
                if not isinstance(layer, TileLayer):
                    raise RuntimeError('game_layer has unexpected type')
                return layer
        raise RuntimeError('ItemManager should always have a game layer')


class ItemReference:
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

    @property
    def game_layer(self) -> bool:
        return False


class Tile:
    def __init__(self, x: int, y: int, tile_type: Type[CTileVanilla], data: StringFile):
        pass


class TileLayer(ItemLayer):
    def __init__(self,
                 width: int,
                 height: int,
                 flags: list[EnumTileLayerFlags] = [],
                 color_envelope_ref: Optional[ItemEnvelope | int] = None,
                 image_ref: Optional[ItemImage | int] = None,
                 color_envelope_offset: int = 0,
                 color: ColorTuple = (0, 0, 0, 0),
                 detail: bool = False,
                 name: str = '',
                 tile_data: Optional[bytes] = None):
        self._width = width
        self._height = height
        self._flags = flags  # TODO: individual getters as in game_layer

        # TODO: getters/setters
        # self._color_envelope_ref = color_envelope_ref
        # self._image_ref = image_ref

        self.color = color
        self.detail = detail
        self._name = name

        if tile_data:
            self._tile_data = StringFile(tile_data)
        else:
            # TODO: this is only vanilla case
            self._tile_data = StringFile(bytes(width * height * 4))

        # TODO: resize
        # TODO: how efficient is this for many tiles? -> maybe create a tile buffer region which only blits on demand

    def get_tile(self, x: int, y: int):

        tile_type = CTileVanilla
        # if self.tele_layer -> CTileTele
        # self._tile_data.seek(x * y * tile_type.size_bytes())
        return Tile(x, y, tile_type, self._tile_data)

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def game_layer(self):
        return EnumTileLayerFlags.GAME in self._flags

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        assert c_intstr3.fits_str(value)
        self._name = value


class QuadLayer(ItemLayer):
    pass


class SoundLayer(ItemLayer):
    pass


class ItemGroup(Item):
    def __init__(self,
                 layers: list[ItemLayer] | list[int],
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
