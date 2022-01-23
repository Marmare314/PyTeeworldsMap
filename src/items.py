from PIL import Image
from typing import Optional

from structs import c_intstr3
from tilemanager import SpeedupTileManager, SwitchTileManager, TeleTileManager, TileManager, TuneTileManager, VanillaTileManager

ColorTuple = tuple[int, int, int, int]


# TODO: make sure references are internal and valid
class ItemManager:
    def __init__(self):
        self._item_set: set[Item] = set()

        version = ItemVersion(3)
        info = ItemInfo()
        game_layer = TileLayer(100, 100, is_game=True, name='Game')
        game_group = ItemGroup([game_layer], name='Game')

        self.add(version)
        self.add(info)
        self.add(game_group)

    def find_item(self, id: int):
        pass  # TODO

    def _generate_id(self, item: 'Item'):
        pass  # TODO

    def add(self, item: 'Item'):
        if item._has_id:  # type: ignore
            item_id: int = item._item_id  # type: ignore
            stored_item = self.find_item(item_id)
            if stored_item:
                self._item_set.remove(stored_item)
            self._item_set.add(item)
        else:
            self._generate_id(item)
            self._item_set.add(item)

    def clear(self):
        self._item_set = set()

    @property
    def info(self):
        for item in self._item_set:
            if isinstance(item, ItemInfo):
                return item
        raise RuntimeError('ItemManager should always have an info item')

    @property
    def layers(self):
        for item in self._item_set:
            if isinstance(item, ItemLayer):
                yield item

    @property
    def game_layer(self) -> 'VanillaTileLayer':
        for layer in self.layers:
            if not isinstance(layer, VanillaTileLayer):
                raise RuntimeError('game_layer has unexpected type')
            return layer
        raise RuntimeError('ItemManager should always have a game layer')


class Item:
    def __init__(self):
        self._has_id = False

    @property
    def _item_id(self):
        return self.__item_id

    @_item_id.setter
    def _item_id(self, value: int):
        self._has_id = True
        self.__item_id = value

    @property
    def _item_manager(self) -> ItemManager:
        return self.__item_manager

    @_item_manager.setter
    def _item_manager(self, value: ItemManager):
        self.__item_manager = value


class ItemVersion(Item):
    def __init__(self, version: int):
        super().__init__()

        self.version = version


class ItemInfo(Item):
    def __init__(self,
                 author: str = '',
                 mapversion: str = '',
                 credits: str = '',
                 license: str = '',
                 settings: list[str] = []):
        super().__init__()

        self.author = author
        self.mapversion = mapversion
        self.credits = credits
        self.license = license
        self.settings = settings  # TODO: a nicer interface for this?

    def __repr__(self):
        return f"<item_info: author='{self.author}', mapversion='{self.mapversion}', credits='{self.credits}', license='{self.license}', settings={self.settings}>"


class ItemImage(Item):
    def __init__(self):
        super().__init__()

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
    def __init__(self):
        super().__init__()


class ItemLayer(Item):
    def __init__(self, detail: bool = False):
        super().__init__()

        self.detail = detail

    @property
    def is_game(self) -> bool:
        return False


class TileLayer(ItemLayer):
    def __init__(self,
                 width: int,
                 height: int,
                 color_envelope_ref: Optional[ItemEnvelope | int] = None,
                 image_ref: Optional[ItemImage | int] = None,
                 color_envelope_offset: int = 0,
                 color: ColorTuple = (0, 0, 0, 0),
                 detail: bool = False,
                 is_game: bool = False,
                 is_tele: bool = False,
                 is_speedup: bool = False,
                 is_front: bool = False,
                 is_switch: bool = False,
                 is_tune: bool = False,
                 name: str = ''):
        super().__init__(detail)

        self._init_flags()
        self.is_game = is_game
        self.is_tele = is_tele
        self.is_speedup = is_speedup
        self.is_front = is_front
        self.is_switch = is_switch
        self.is_tune = is_tune

        # TODO: getters/setters
        # self._color_envelope_ref = color_envelope_ref
        # self._image_ref = image_ref

        self._color_envelope_offset = color_envelope_offset
        self.color = color
        self._name = name

        # TODO: this is a bit memory inefficient when loading a file
        self._tiles = TileManager(width, height, bytes(width * height))

    def _init_flags(self):
        self._is_game = False
        self._is_tele = False
        self._is_speedup = False
        self._is_front = False
        self._is_switch = False
        self._is_tune = False

    @property
    def width(self):
        return self._tiles.width

    @property
    def height(self):
        return self._tiles.height

    def _any_layer_flag(self):
        return self.is_game or self.is_tele or self.is_speedup or self.is_front or self.is_switch or self.is_tune

    @property
    def is_game(self):
        return self._is_game

    @is_game.setter
    def is_game(self, value: bool):
        if value and self._any_layer_flag() and not self.is_game:
            raise ValueError('Only one layer flag can be set at a time')

        # TODO: also make sure that there is exactly one game layer in the itmemmanager

        self._is_game = value

    @property
    def is_tele(self):
        return self._is_tele

    @is_tele.setter
    def is_tele(self, value: bool):
        if value and self._any_layer_flag() and not self.is_tele:
            raise ValueError('Only one layer flag can be set at a time')
        self._is_tele = value

    @property
    def is_speedup(self):
        return self._is_speedup

    @is_speedup.setter
    def is_speedup(self, value: bool):
        if value and self._any_layer_flag() and not self.is_speedup:
            raise ValueError('Only one layer flag can be set at a time')
        self._is_speedup = value

    @property
    def is_front(self):
        return self._is_front

    @is_front.setter
    def is_front(self, value: bool):
        if value and self._any_layer_flag() and not self.is_front:
            raise ValueError('Only one layer flag can be set at a time')
        self._is_front = value

    @property
    def is_switch(self):
        return self._is_switch

    @is_switch.setter
    def is_switch(self, value: bool):
        if value and self._any_layer_flag() and not self.is_switch:
            raise ValueError('Only one layer flag can be set at a time')
        self._is_switch = value

    @property
    def is_tune(self):
        return self._is_tune

    @is_tune.setter
    def is_tune(self, value: bool):
        if value and self._any_layer_flag() and not self.is_tune:
            raise ValueError('Only one layer flag can be set at a time')
        self._is_tune = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        assert c_intstr3.fits_str(value)
        self._name = value


class VanillaTileLayer(TileLayer):
    @property
    def tiles(self):
        return self._tiles

    @tiles.setter
    def tiles(self, tiles: VanillaTileManager):
        self._tiles = tiles


class TeleTileLayer(TileLayer):
    @property
    def tiles(self):
        return self._tiles

    @tiles.setter
    def tiles(self, tiles: TeleTileManager):
        self._tiles = tiles


class SpeedupTileLayer(TileLayer):
    @property
    def tiles(self):
        return self._tiles

    @tiles.setter
    def tiles(self, tiles: SpeedupTileManager):
        self._tiles = tiles


class SwitchTileLayer(TileLayer):
    @property
    def tiles(self):
        return self._tiles

    @tiles.setter
    def tiles(self, tiles: SwitchTileManager):
        self._tiles = tiles


class TuneTileLayer(TileLayer):
    @property
    def tiles(self):
        return self._tiles

    @tiles.setter
    def tiles(self, tiles: TuneTileManager):
        self._tiles = tiles


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
        super().__init__()


class ItemSound(Item):
    def __init__(self):
        super().__init__()
