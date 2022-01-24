# pyright: reportPrivateUsage=false

from PIL import Image
from typing import Callable, Optional, Type, TypeVar
from itertools import count, filterfalse

from structs import c_intstr3, c_int32
from tilemanager import SpeedupTileManager, SwitchTileManager, TeleTileManager, TileManager, TuneTileManager, VanillaTileManager
from constants import EnumTileLayerFlags


T = TypeVar('T', bound='Item')
S = TypeVar('S')


ColorTuple = tuple[int, int, int, int]


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

    def find_item(self, item_type: 'Type[Item]', id: int):
        for item in self._item_set:
            if item._item_id == id and isinstance(item, item_type):
                return item

    def map(self, item_type: Type[T], f: Callable[[T], S]) -> list[S]:
        ret_list: list[S] = []
        for item in self._item_set:
            if isinstance(item, item_type):
                ret_list.append(f(item))
        return ret_list

    def _get_ids_type(self, item_type: 'Type[Item]'):
        ids: set[int] = set()
        for item in self._item_set:
            if type(item) == item_type:
                ids.add(item._item_id)
        return ids

    def _next_free_id(self, item_type: 'Type[Item]'):
        ids = self._get_ids_type(item_type)
        return next(filterfalse(set(ids).__contains__, count(0)))

    def _generate_id(self, item: 'Item'):
        new_id = self._next_free_id(type(item))
        item._item_id = new_id

    def minimize_ids(self):
        pass

    def add(self, item: 'Item'):
        if item._has_manager:
            if item._item_manager != self:
                pass  # copy item and that one instead
        else:
            item._item_manager = self

        if item._has_id:
            item_id: int = item._item_id
            stored_item = self.find_item(type(item), item_id)
            if stored_item:
                self._item_set.remove(stored_item)
            self._item_set.add(item)
        else:
            self._generate_id(item)
            self._item_set.add(item)

        item._add_references()
        item._validate_references()
        item._validate_data()

    def clear(self):
        self._item_set = set()

    @property
    def version(self):
        for item in self._item_set:
            if isinstance(item, ItemVersion):
                return item
        raise RuntimeError('ItemManager should always have a version item')

    @property
    def info(self):
        for item in self._item_set:
            if isinstance(item, ItemInfo):
                return item
        raise RuntimeError('ItemManager should always have an info item')

    @property
    def images(self):
        for item in sorted(self._item_set):
            if isinstance(item, ItemImage):
                yield item

    @property
    def _layers(self):
        for item in sorted(self._item_set):
            if isinstance(item, ItemLayer):
                yield item

    @property
    def groups(self):
        for item in sorted(self._item_set):
            if isinstance(item, ItemGroup):
                yield item

    @property
    def game_layer(self) -> 'VanillaTileLayer':
        for layer in self._layers:
            if layer.is_game:
                if not isinstance(layer, VanillaTileLayer):
                    raise RuntimeError('game_layer has unexpected type')
                return layer
        raise RuntimeError('ItemManager should always have a game layer')


class Item:
    def __init__(self):
        self._has_id = False
        self._has_manager = False

    def __lt__(self, other: 'Item'):
        return self._item_id < other._item_id

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
        self._has_manager = True
        self.__item_manager = value

    def _expect_manager(self):
        if not self._has_manager:
            raise RuntimeError('expected item to have a manager')

    def _expect_id(self):
        if not self._has_id:
            raise RuntimeError('expected item to have an id')

    def _validate_ref(self, item: 'Item'):
        self._expect_manager()
        item._expect_manager()
        item._expect_id()
        if self._item_manager != item._item_manager:
            raise ValueError('items should be managed by the same manager')
        if self._item_manager.find_item(type(item), item.__item_id) is None:
            raise ValueError('Referenced item not valid')

    def _add_ref(self, item: 'Item'):
        self._expect_manager()
        self._item_manager.add(item)

    def _validate_references(self):
        pass

    def _add_references(self):
        pass

    def _set_references_import(self, manager: ItemManager):
        self._item_manager = manager

    def _validate_data(self):
        pass


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
        return f"<item_info>"


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
    def __init__(self, detail: bool = False, name: str = ''):
        super().__init__()

        self.detail = detail
        self._name = name

    @property
    def is_game(self) -> bool:
        return False

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        assert c_intstr3.fits_str(value)
        self._name = value


class TileLayer(ItemLayer):
    def __init__(self,
                 width: int,
                 height: int,
                 color_envelope_ref: Optional[ItemEnvelope] = None,
                 image_ref: Optional[ItemImage] = None,
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
        super().__init__(detail, name)

        self._reset_all_flags()
        self.is_game = is_game
        self.is_tele = is_tele
        self.is_speedup = is_speedup
        self.is_front = is_front
        self.is_switch = is_switch
        self.is_tune = is_tune

        self._color_envelope_ref = color_envelope_ref
        self._image_ref = image_ref

        self._color_envelope_offset = color_envelope_offset
        self.color = color

        # TODO: this is a bit memory inefficient when loading a file
        self._tiles = TileManager(width, height, bytes(width * height))

    @property
    def color_envelope(self):
        return self._color_envelope_ref

    @color_envelope.setter
    def color_envelope(self, item: Optional[ItemEnvelope]):
        if item:
            self._validate_ref(item)
        self._color_envelope_ref = item

    @property
    def image(self):
        self._image_ref

    @image.setter
    def image(self, item: Optional[ItemImage]):
        if item:
            self._validate_ref(item)
        self._image_ref = item

    def _add_references(self):
        if self._image_ref:
            self._add_ref(self._image_ref)
        if self._color_envelope_ref:
            self._add_ref(self._color_envelope_ref)

    def _validate_references(self):
        if self._image_ref:
            self._validate_ref(self._image_ref)
        if self._color_envelope_ref:
            self._validate_ref(self._color_envelope_ref)

    def _set_references_import(self, manager: ItemManager):
        super()._set_references_import(manager)

        self._expect_manager()

        if self._image_ref:
            self._image_ref = self._item_manager.find_item(ItemImage, self._image_ref._item_id)
        if self._color_envelope_ref:
            self._color_envelope_ref = self._item_manager.find_item(ItemImage, self._color_envelope_ref._item_id)

    def _validate_data(self):
        self._expect_manager()

        for flag in EnumTileLayerFlags:
            flags = self._item_manager.map(TileLayer, lambda s: TileLayer._get_flag(s, flag))
            assert sum(flags) <= 1

    @property
    def width(self):
        return self._tiles.width

    @property
    def height(self):
        return self._tiles.height

    def _get_flag(self, flag: EnumTileLayerFlags):
        if flag == EnumTileLayerFlags.GAME:
            return self._is_game
        elif flag == EnumTileLayerFlags.TELE:
            return self._is_tele
        elif flag == EnumTileLayerFlags.SPEEDUP:
            return self._is_speedup
        elif flag == EnumTileLayerFlags.FRONT:
            return self._is_front
        elif flag == EnumTileLayerFlags.SWITCH:
            return self._is_switch
        elif flag == EnumTileLayerFlags.TUNE:
            return self._is_tune

    def _set_flag(self, flag: EnumTileLayerFlags, value: bool):
        if flag == EnumTileLayerFlags.GAME:
            self._is_game = value
        elif flag == EnumTileLayerFlags.TELE:
            self._is_tele = value
        elif flag == EnumTileLayerFlags.SPEEDUP:
            self._is_speedup = value
        elif flag == EnumTileLayerFlags.FRONT:
            self._is_front = value
        elif flag == EnumTileLayerFlags.SWITCH:
            self._is_switch = value
        elif flag == EnumTileLayerFlags.TUNE:
            self._is_tune = value

    def _reset_all_flags(self):
        for flag in EnumTileLayerFlags:
            self._set_flag(flag, False)

    def _flag_setter(self, flag: EnumTileLayerFlags, value: bool):
        if not self._has_manager:
            self._set_flag(flag, value)
        else:
            if value:
                self._reset_all_flags()
                self._item_manager.map(TileLayer, lambda s: TileLayer._set_flag(s, flag, False))
            else:
                if self._get_flag(flag):
                    raise RuntimeError('the flag will be removed automatically if another one is set')
            self._set_flag(flag, value)

    @property
    def is_game(self):
        return self._get_flag(EnumTileLayerFlags.GAME)

    @is_game.setter
    def is_game(self, value: bool):
        self._flag_setter(EnumTileLayerFlags.GAME, value)

    @property
    def is_tele(self):
        return self._get_flag(EnumTileLayerFlags.TELE)

    @is_tele.setter
    def is_tele(self, value: bool):
        self._flag_setter(EnumTileLayerFlags.TELE, value)

    @property
    def is_speedup(self):
        return self._get_flag(EnumTileLayerFlags.SPEEDUP)

    @is_speedup.setter
    def is_speedup(self, value: bool):
        self._flag_setter(EnumTileLayerFlags.SPEEDUP, value)

    @property
    def is_front(self):
        return self._get_flag(EnumTileLayerFlags.FRONT)

    @is_front.setter
    def is_front(self, value: bool):
        self._flag_setter(EnumTileLayerFlags.FRONT, value)

    @property
    def is_switch(self):
        return self._get_flag(EnumTileLayerFlags.SWITCH)

    @is_switch.setter
    def is_switch(self, value: bool):
        self._flag_setter(EnumTileLayerFlags.SWITCH, value)

    @property
    def is_tune(self):
        return self._get_flag(EnumTileLayerFlags.TUNE)

    @is_tune.setter
    def is_tune(self, value: bool):
        self._flag_setter(EnumTileLayerFlags.TUNE, value)

    def __repr__(self):
        if self.name:
            return f'<tile_layer: {self.name}>'
        else:
            return f'<tile_layer: [{self._item_id}]>'


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
                 layers: list[ItemLayer],
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

        self._layers = list(sorted(layers))
        self._x_offset = x_offset
        self._y_offset = y_offset
        self._x_parallax = x_parallax
        self._y_parallax = y_parallax
        self.clipping = clipping
        self._clip_x = clip_x
        self._clip_y = clip_y
        self._clip_width = clip_width
        self._clip_height = clip_height
        self._name = name

    def _add_references(self):
        for layer in self._layers:
            self._add_ref(layer)

    def _validate_references(self):
        for layer in self._layers:
            self._validate_ref(layer)

    def _set_references_import(self, manager: ItemManager):
        super()._set_references_import(manager)

        self._expect_manager()

        new_layers: list[ItemLayer] = []
        for layer in self._layers:
            new_layer = self._item_manager.find_item(ItemLayer, layer._item_id)
            if new_layer and isinstance(new_layer, ItemLayer):
                new_layers.append(new_layer)
            else:
                raise RuntimeError('invalid reference on import')
        self._layers = new_layers

    @property
    def layers(self):
        return list(self._layers)

    @property
    def x_offset(self):
        return self._x_offset

    @x_offset.setter
    def x_offset(self, value: int):
        assert c_int32.fits_value(value)
        self._x_offset = value

    @property
    def y_offset(self):
        return self._y_offset

    @y_offset.setter
    def y_offset(self, value: int):
        assert c_int32.fits_value(value)
        self._y_offset = value

    @property
    def x_parallax(self):
        return self._x_parallax

    @x_parallax.setter
    def x_parallax(self, value: int):
        assert c_int32.fits_value(value)
        self._x_parallax = value

    @property
    def y_parallax(self):
        return self._y_parallax

    @y_parallax.setter
    def y_parallax(self, value: int):
        assert c_int32.fits_value(value)
        self._y_parallax = value

    @property
    def clip_x(self):
        return self._clip_x

    @clip_x.setter
    def clip_x(self, value: int):
        assert c_int32.fits_value(value)
        self._clip_x = value

    @property
    def clip_y(self):
        return self._clip_y

    @clip_y.setter
    def clip_y(self, value: int):
        assert c_int32.fits_value(value)
        self._clip_y = value

    @property
    def clip_width(self):
        return self._clip_width

    @clip_width.setter
    def clip_width(self, value: int):
        assert c_int32.fits_value(value)
        self._clip_width = value

    @property
    def clip_height(self):
        return self._clip_height

    @clip_height.setter
    def clip_height(self, value: int):
        assert c_int32.fits_value(value)
        self._clip_height = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        assert c_intstr3.fits_str(value)
        self._name = value

    def __repr__(self):
        if self.name:
            print(bytes(self.name, 'utf8'))
            return f'<Group: {self.name}>'
        else:
            return f'<Group: [{self._item_id}]>'


class ItemSound(Item):
    def __init__(self):
        super().__init__()
