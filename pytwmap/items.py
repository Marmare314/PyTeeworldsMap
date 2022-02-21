from PIL import Image
from typing import Generic, Optional, TypeVar, Tuple, List
import os

from pytwmap.structs import c_intstr3, c_int32
from pytwmap.tilemanager import TileManager


TITEM = TypeVar('TITEM', bound='Item')
TMANAGER = TypeVar('TMANAGER', bound=TileManager)


TPoint = Tuple[int, int]
TColor = Tuple[int, int, int, int]


class Item:
    pass


class ItemVersion(Item):
    def __init__(self, version: int):
        self.version = version

    def __repr__(self):
        return f'<item_version: {self.version}>'


class ItemInfo(Item):
    def __init__(self,
                 author: str = '',
                 mapversion: str = '',
                 credits: str = '',
                 license: str = '',
                 settings: 'list[str]' = []):
        self.author = author
        self.mapversion = mapversion
        self.credits = credits
        self.license = license
        self.settings = settings  # TODO: a nicer interface for this?

    def __repr__(self):
        return f'<item_info>'


class ItemImage(Item):
    def __init__(self):
        raise NotImplementedError()

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
    def __init__(self, image: Image.Image, name: str,):
        self.set_internal(image, name)

    @ItemImage.name.setter
    def name(self, name: str):
        # TODO: check if name is valid
        self._name = name

    def __repr__(self):
        if self.name:
            return f'<image_internal: {self.name}>'
        else:
            return f'<image_internal: {hex(id(self))}>'


class ItemImageExternal(ItemImage):
    def __init__(self, name: str):
        self.set_external(name)

    def __repr__(self):
        if self.name:
            return f'<image_external: {self.name}>'
        else:
            return f'<image_external: {hex(id(self))}>'


class ItemEnvelope(Item):
    pass


class ItemLayer(Item):
    def __init__(self, detail: bool = False, name: str = ''):
        self.detail = detail
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        assert c_intstr3.fits_str(value)
        self._name = value


class ItemTileLayer(ItemLayer, Generic[TMANAGER]):
    def __init__(self,
                 tiles: TMANAGER,
                 color_envelope_ref: Optional[ItemEnvelope] = None,
                 image_ref: Optional[ItemImage] = None,
                 color_envelope_offset: int = 0,
                 color: TColor = (255, 255, 255, 255),
                 detail: bool = False,
                 name: str = ''):
        super().__init__(detail, name)

        self._color_envelope_ref = color_envelope_ref
        self._image_ref = image_ref

        self._color_envelope_offset = color_envelope_offset
        self.color = color

        self._tiles = tiles

    # TODO: should these be properties -> typechecked or just have them be variables
    @property
    def color_envelope(self):
        self._color_envelope_ref

    @color_envelope.setter
    def color_envelope(self, item: Optional[ItemEnvelope]):
        self._color_envelope_ref = item

    @property
    def image(self):
        return self._image_ref

    @image.setter
    def image(self, item: Optional[ItemImage]):
        self._image_ref = item

    @property
    def color_envelope_offset(self):
        return self._color_envelope_offset

    @color_envelope_offset.setter
    def color_envelope_offset(self, value: int):
        assert c_int32.fits_value(value)
        self._color_envelope_offset = value

    @property
    def width(self):
        return self._tiles.width

    @property
    def height(self):
        return self._tiles.height

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
            return f'<tile_layer: {hex(id(self))}>'


class ItemQuad(Item):
    def __init__(self,
                 corners: Tuple[TPoint, TPoint, TPoint, TPoint],
                 pivot: TPoint,
                 corner_colors: Tuple[TColor, TColor, TColor, TColor],
                 texture_coordinates: Tuple[TPoint, TPoint, TPoint, TPoint],
                 position_envelope_ref: Optional[ItemEnvelope] = None,
                 position_envelope_offset: int = 0,
                 color_envelope_ref: Optional[ItemEnvelope] = None,
                 color_envelope_offset: int = 0):
        self.corners = corners
        self.pivot = pivot
        self.corner_colors = corner_colors
        self.texture_coords = texture_coordinates
        self.position_envelope_ref = position_envelope_ref
        self.position_envelope_offset = position_envelope_offset
        self.color_envelope_ref = color_envelope_ref
        self.color_envelope_offset = color_envelope_offset


class ItemQuadLayer(ItemLayer):
    def __init__(self,
                 quads: List[ItemQuad],
                 image_ref: Optional[ItemImage] = None,
                 detail: bool = False,
                 name: str = ''):
        super().__init__(detail, name)

        self.quads = quads
        self.image = image_ref

    @property
    def image(self):
        return self._image_ref

    @image.setter
    def image(self, item: Optional[ItemImage]):
        self._image_ref = item

    def __repr__(self):
        if self.name:
            return f'<quad_layer: {self.name}>'
        else:
            return f'<quad_layer: {hex(id(self))}>'


class ItemSoundLayer(ItemLayer):
    pass


class ItemGroup(Item):
    def __init__(self,
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
                 name: str = ''):
        self.layers = layers
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
            return f'<group: {self.name}>'
        else:
            return f'<group: {hex(id(self))}>'


class ItemSound(Item):
    pass
