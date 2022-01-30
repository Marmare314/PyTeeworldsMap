from PIL import Image
from typing import Callable, Generic, Optional, Type, TypeVar, Tuple
from itertools import count, filterfalse
import os

from pytwmap.structs import c_intstr3, c_int32
from pytwmap.tilemanager import TileManager, VanillaTileManager
from pytwmap.constants import TileLayerFlags


TITEM = TypeVar('TITEM', bound='Item')
TMANAGER = TypeVar('TMANAGER', bound=TileManager)


ColorTuple = Tuple[int, int, int, int]


class ItemManager:
    def __init__(self):
        self._item_set: set[Item] = set()

        ItemVersion(manager=self, version=1)
        ItemInfo(manager=self)
        game_layer = ItemTileLayer(
            manager=self,
            tiles=VanillaTileManager(50, 50),
            is_game=True,
            name='Game'
        )
        ItemGroup(
            manager=self,
            layers=[game_layer],
            name='Game'
        )

    def find_item(self, item_type: 'Type[TITEM]', id: int) -> Optional[TITEM]:
        for item in self._item_set:
            if item.item_id == id and isinstance(item, item_type):
                return item

    def map(self, item_type: Type[TITEM], f: Callable[[TITEM], None]):
        for item in self._item_set:
            if isinstance(item, item_type):
                f(item)

    def _get_ids_type(self, item_type: 'Type[Item]'):
        ids: set[int] = set()
        for item in self._item_set:
            if type(item) == item_type:
                ids.add(item.item_id)
        return ids

    def _next_free_id(self, item_type: 'Type[Item]'):
        ids = self._get_ids_type(item_type)
        return next(filterfalse(set(ids).__contains__, count(0)))

    def clean_ids(self):
        for i, image in enumerate(self.images):
            image.item_id = i

        for i, group in enumerate(self.groups):
            group.item_id = i

        total_layers = 0
        for group in self.groups:
            for i, layer in enumerate(group.layers):
                layer.item_id = total_layers + i
            total_layers += len(group.layers)

    # TODO: make sure that only one version item with id=0 is registered (also info)
    def register(self, item: 'Item'):
        if item.manager != self:
            raise NotImplementedError()  # TODO: add copy of item
        else:
            generated_id = self._next_free_id(type(item))
            self._item_set.add(item)
            return generated_id

    def register_with_id(self, item: 'Item', id: int):
        if id in self._get_ids_type(type(item)):
            raise RuntimeError('id already used')
        self._item_set.add(item)

    def validate(self, item: 'Item'):
        pass  # TODO

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
    def layers(self):
        for item in sorted(self._item_set):
            if isinstance(item, ItemLayer):
                yield item

    @property
    def groups(self):
        for item in sorted(self._item_set):
            if isinstance(item, ItemGroup):
                yield item

    @property
    def game_layer(self) -> 'ItemTileLayer[VanillaTileManager]':
        for layer in self.layers:
            if layer.is_game:
                if not isinstance(layer, ItemTileLayer):
                    raise RuntimeError('game_layer has unexpected type')
                return layer  # type: ignore  # TODO: check type arg somehow (get_args?)
        raise RuntimeError('ItemManager should always have a game layer')


class Item:
    def __init__(self, manager: ItemManager, _id: Optional[int] = None):
        self._item_manager = manager
        if _id is not None:
            self._item_manager.register_with_id(self, _id)
            self._item_id = _id
        else:
            self._item_id = self._item_manager.register(self)

    def __lt__(self, other: 'Item'):
        return self._item_id < other._item_id

    @property
    def manager(self):
        return self._item_manager

    @property
    def item_id(self):
        """ getter for internal id

        Returns:
            int: _item_id
        """

        return self._item_id

    @item_id.setter
    def item_id(self, new_id: int):
        """ CAUTION: this changes the internal id without any error checking (this should probably not be done)

        setter for internal id

        Args:
            new_id (int): new internal id
        """

        self._item_id = new_id


class ItemVersion(Item):
    def __init__(self,
                 manager: ItemManager,
                 version: int,
                 _id: Optional[int] = None):
        super().__init__(manager, _id)

        self.version = version


class ItemInfo(Item):
    def __init__(self,
                 manager: ItemManager,
                 author: str = '',
                 mapversion: str = '',
                 credits: str = '',
                 license: str = '',
                 settings: 'list[str]' = [],
                 _id: Optional[int] = None):
        super().__init__(manager, _id)

        self.author = author
        self.mapversion = mapversion
        self.credits = credits
        self.license = license
        self.settings = settings  # TODO: a nicer interface for this?

    def __repr__(self):
        return f"<item_info>"


class ItemImage(Item):
    def __init__(self, manager: ItemManager, _id: Optional[int] = 0):
        super().__init__(manager, _id)

    def set_internal(self, image: Image.Image, name: str):
        self._image = image
        self._name = name
        self._external = False

    @staticmethod
    def _remove_file_extension(name: str):
        if name.endswith('.png'):
            return name[:-4]
        raise RuntimeError('Invalid file extension')

    @staticmethod
    def _directory_has_image(path: str, name: str):
        files = [ItemImage._remove_file_extension(x) for x in os.listdir(path)]
        return name in files

    @staticmethod
    def _get_external_path(name: str):  # TODO: if 07 is supported this needs to be changed
        path_06 = os.path.join(os.path.dirname(__file__), 'mapres_06')
        if ItemImage._directory_has_image(path_06, name):
            return os.path.join(os.path.dirname(__file__), f'mapres_06/{name}.png')
        else:
            raise RuntimeError('not a valid external image name')

    def set_external(self, name: str):
        self._image = Image.open(self._get_external_path(name))
        self._name = name
        self._external = True

    @property
    def external(self):
        return self._external

    @property
    def image(self):
        return self._image

    @property
    def name(self):
        return self._name

    @property
    def width(self):
        return self._image.width

    @property
    def height(self):
        return self._image.height


class ItemImageInternal(ItemImage):
    def __init__(self,
                 manager: ItemManager,
                 image: Image.Image,
                 name: str,
                 _id: Optional[int] = None):
        super().__init__(manager, _id)
        self.set_internal(image, name)

    @ItemImage.name.setter
    def name(self, name: str):
        # TODO: check if name is valid
        self._name = name


class ItemImageExternal(ItemImage):
    def __init__(self,
                 manager: ItemManager,
                 name: str,
                 _id: Optional[int] = None):
        super().__init__(manager, _id)
        self.set_external(name)


class ItemEnvelope(Item):
    def __init__(self, manager: ItemManager, _id: Optional[int] = None):
        super().__init__(manager, _id)


class ItemLayer(Item):
    def __init__(self,
                 manager: ItemManager,
                 detail: bool = False,
                 name: str = '',
                 _id: Optional[int] = None):
        super().__init__(manager, _id)

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


class ItemTileLayer(ItemLayer, Generic[TMANAGER]):
    def __init__(self,
                 manager: ItemManager,
                 tiles: TMANAGER,
                 color_envelope_ref: Optional[ItemEnvelope] = None,
                 image_ref: Optional[ItemImage] = None,
                 color_envelope_offset: int = 0,
                 color: ColorTuple = (255, 255, 255, 255),
                 detail: bool = False,
                 is_game: bool = False,
                 is_tele: bool = False,
                 is_speedup: bool = False,
                 is_front: bool = False,
                 is_switch: bool = False,
                 is_tune: bool = False,
                 name: str = '',
                 _id: Optional[int] = None):
        super().__init__(manager, detail, name, _id=_id)

        self._reset_all_flags()
        self.is_game = is_game
        self.is_tele = is_tele
        self.is_speedup = is_speedup
        self.is_front = is_front
        self.is_switch = is_switch
        self.is_tune = is_tune
        # TODO: was this actually needed self._validate_flags()?

        self._color_envelope_ref = color_envelope_ref
        self._image_ref = image_ref

        self._color_envelope_offset = color_envelope_offset
        self.color = color

        self._tiles = tiles

    @property
    def color_envelope(self):
        return self._color_envelope_ref

    @color_envelope.setter
    def color_envelope(self, item: Optional[ItemEnvelope]):
        if item:
            self._item_manager.validate(item)
        self._color_envelope_ref = item

    @property
    def color_envelope_offset(self):
        return self._color_envelope_offset

    @color_envelope_offset.setter
    def color_envelope_offset(self, value: int):
        assert c_int32.fits_value(value)
        self._color_envelope_offset = value

    @property
    def image(self):
        return self._image_ref

    @image.setter
    def image(self, item: Optional[ItemImage]):
        if item:
            self._item_manager.validate(item)
        self._image_ref = item

    @property
    def width(self):
        return self._tiles.width

    @property
    def height(self):
        return self._tiles.height

    def _get_flag(self, flag: TileLayerFlags):
        if flag == TileLayerFlags.GAME:
            return self._is_game
        elif flag == TileLayerFlags.TELE:
            return self._is_tele
        elif flag == TileLayerFlags.SPEEDUP:
            return self._is_speedup
        elif flag == TileLayerFlags.FRONT:
            return self._is_front
        elif flag == TileLayerFlags.SWITCH:
            return self._is_switch
        elif flag == TileLayerFlags.TUNE:
            return self._is_tune

    def _set_flag(self, flag: TileLayerFlags, value: bool):
        if flag == TileLayerFlags.GAME:
            self._is_game = value
        elif flag == TileLayerFlags.TELE:
            self._is_tele = value
        elif flag == TileLayerFlags.SPEEDUP:
            self._is_speedup = value
        elif flag == TileLayerFlags.FRONT:
            self._is_front = value
        elif flag == TileLayerFlags.SWITCH:
            self._is_switch = value
        elif flag == TileLayerFlags.TUNE:
            self._is_tune = value

    def _reset_all_flags(self):
        for flag in TileLayerFlags:
            self._set_flag(flag, False)

    def _flag_setter(self, flag: TileLayerFlags, value: bool):
        if value:
            self._reset_all_flags()
            self._item_manager.map(ItemTileLayer, lambda s: ItemTileLayer._set_flag(s, flag, False))  # type: ignore
        elif flag == TileLayerFlags.GAME and self._get_flag(flag):
            raise RuntimeError('the game flag will be automatically removed if it is set on another layer')
        self._set_flag(flag, value)

    @property
    def is_game(self):
        return self._get_flag(TileLayerFlags.GAME)

    @is_game.setter
    def is_game(self, value: bool):
        self._flag_setter(TileLayerFlags.GAME, value)

    @property
    def is_tele(self):
        return self._get_flag(TileLayerFlags.TELE)

    @is_tele.setter
    def is_tele(self, value: bool):
        self._flag_setter(TileLayerFlags.TELE, value)

    @property
    def is_speedup(self):
        return self._get_flag(TileLayerFlags.SPEEDUP)

    @is_speedup.setter
    def is_speedup(self, value: bool):
        self._flag_setter(TileLayerFlags.SPEEDUP, value)

    @property
    def is_front(self):
        return self._get_flag(TileLayerFlags.FRONT)

    @is_front.setter
    def is_front(self, value: bool):
        self._flag_setter(TileLayerFlags.FRONT, value)

    @property
    def is_switch(self):
        return self._get_flag(TileLayerFlags.SWITCH)

    @is_switch.setter
    def is_switch(self, value: bool):
        self._flag_setter(TileLayerFlags.SWITCH, value)

    @property
    def is_tune(self):
        return self._get_flag(TileLayerFlags.TUNE)

    @is_tune.setter
    def is_tune(self, value: bool):
        self._flag_setter(TileLayerFlags.TUNE, value)

    @property
    def tiles(self):
        return self._tiles

    @tiles.setter
    def tiles(self, tiles: TMANAGER):
        self._tiles = tiles

    def __repr__(self):
        if self.name:
            return f'<tile_layer: {self.name}>'
        else:
            return f'<tile_layer: [{self._item_id}]>'


class ItemQuadLayer(ItemLayer):
    pass


class ItemSoundLayer(ItemLayer):
    pass


class ItemGroup(Item):
    def __init__(self,
                 manager: ItemManager,
                 layers: 'list[ItemLayer]',
                 x_offset: int = 0,
                 y_offset: int = 0,
                 x_parallax: int = 100,
                 y_parallax: int = 100,
                 clipping: bool = False,
                 clip_x: int = 0,
                 clip_y: int = 0,
                 clip_width: int = 0,
                 clip_height: int = 0,
                 name: str = '',
                 _id: Optional[int] = None):
        super().__init__(manager, _id)

        self._layers = layers
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.x_parallax = x_parallax
        self.y_parallax = y_parallax
        self.clipping = clipping
        self.clip_x = clip_x
        self.clip_y = clip_y
        self.clip_width = clip_width
        self.clip_height = clip_height
        self._name = name

    @property
    def layers(self):
        return list(sorted(self._layers))

    def add_layer(self, item: ItemLayer):
        if item:
            self._item_manager.validate(item)
        self._layers.append(item)

    # TODO: valuerange is limited if this is the gamegroup
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
            return f'<Group: {self.name}>'
        else:
            return f'<Group: [{self._item_id}]>'


class ItemSound(Item):
    def __init__(self, manager: ItemManager, _id: Optional[int] = None):
        super().__init__(manager, _id)
