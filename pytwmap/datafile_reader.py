import zlib
from PIL import Image
from typing import Optional, Type, TypeVar

from pytwmap.stringfile import StringFile
from pytwmap.structs import c_int32
from pytwmap.map_structs import CItemEnvelope, CItemGroup, CItemLayer, CItemQuadLayer, CItemSound, CItemSoundLayer, CItemTileLayer, CVersionHeader, CHeader, CItemType, CItemVersion, CItemHeader, CItemInfo, CItemImage, c_struct
from pytwmap.items import ItemEnvelope, ItemGroup, ItemImage, ItemImageExternal, ItemImageInternal, ItemLayer, ItemVersion, ItemInfo, ItemTileLayer
from pytwmap.constants import ItemType, LayerFlags, LayerType, TileLayerFlags
from pytwmap.tilemanager import SpeedupTileManager, SwitchTileManager, TeleTileManager, TuneTileManager, VanillaTileManager


T = TypeVar('T', bound=c_struct)


# TODO: rename with c_item
class DataFileReader:
    def __init__(self, file_data: bytes):
        self._data = StringFile(file_data)

        # init special layer references
        self.game_layer: 'Optional[ItemTileLayer[VanillaTileManager]]' = None
        self.tele_layer: 'Optional[ItemTileLayer[TeleTileManager]]' = None
        self.speedup_layer: 'Optional[ItemTileLayer[SpeedupTileManager]]' = None
        self.front_layer: 'Optional[ItemTileLayer[VanillaTileManager]]' = None
        self.switch_layer: 'Optional[ItemTileLayer[SwitchTileManager]]' = None
        self.tune_layer: 'Optional[ItemTileLayer[TuneTileManager]]' = None

        # item caches
        self._image_cache: 'dict[int, ItemImage]' = {}
        self._layer_cache: 'dict[int, ItemLayer]' = {}

        # read header of datafile
        self._ver_header = CVersionHeader.from_data(self._data)
        if self._ver_header.magic not in ['DATA', 'ATAD']:
            raise RuntimeError('wrong magic bytes')
        if self._ver_header.version != 4:
            raise RuntimeError('only version 4 is supported')

        self._header = CHeader.from_data(self._data)

        self._item_types = [CItemType.from_data(self._data) for _ in range(self._header.num_item_types)]

        self._item_offsets = [c_int32.from_data(self._data) for _ in range(self._header.num_items)]
        self._data_offsets = [c_int32.from_data(self._data) for _ in range(self._header.num_data)]
        self._data_sizes = [c_int32.from_data(self._data) for _ in range(self._header.num_data)]

        self._items_start = self._data.tell()

        self._calc_data_start()

    def _calc_data_start(self):
        self._data_start = self._header.num_item_types * CItemType.size_bytes()
        self._data_start += (self._header.num_items + 2 * self._header.num_data) * c_int32.size_bytes()
        self._data_start += self._header.item_size
        self._data_start += CVersionHeader.size_bytes() + CHeader.size_bytes()

    def _get_data(self, data_ptr: int):
        offset_begin = self._data_offsets[data_ptr]
        offset_end = self._header.size
        if data_ptr + 1 < len(self._data_offsets):
            offset_end = self._data_offsets[data_ptr + 1]
        num_bytes = offset_end - offset_begin

        self._data.seek(self._data_start + offset_begin)
        return zlib.decompress(self._data.read(num_bytes))

    def _get_data_str(self, data_ptr: int):
        if data_ptr < 0:
            return ''
        return self._get_data(data_ptr)[:-1].decode('utf8')

    def _get_data_str_list(self, data_ptr: int) -> 'list[str]':
        if data_ptr < 0:
            return []
        return [s.decode('utf8') for s in self._get_data(data_ptr).split(b'\0')[:-1]]

    def _get_typeid(self, item_type: 'Type[c_struct]'):
        if item_type == CItemVersion:
            return ItemType.VERSION
        elif item_type == CItemInfo:
            return ItemType.INFO
        elif item_type == CItemImage:
            return ItemType.IMAGE
        elif item_type == CItemEnvelope:
            return ItemType.ENVELOPE
        elif item_type == CItemGroup:
            return ItemType.GROUP
        elif item_type in [CItemLayer, CItemTileLayer, CItemQuadLayer, CItemSoundLayer]:
            return ItemType.LAYER
        elif item_type == CItemSound:
            return ItemType.SOUND

    def _get_type_start(self, item_type: 'Type[c_struct]'):
        for c_item in self._item_types:
            if c_item.type_id == self._get_typeid(item_type):
                return c_item.start

    def _get_num_items(self, item_type: 'Type[c_struct]'):
        for c_item in self._item_types:
            if c_item.type_id == self._get_typeid(item_type):
                return c_item.num
        return 0

    def _validate_item_header(self, index: int, item_type: Type[c_struct]):
        if item_type == CItemLayer:
            CItemHeader.from_data(self._data)
            return  # this item will be checked on the second part

        size = item_type.size_bytes()
        if item_type in [CItemTileLayer, CItemQuadLayer, CItemSoundLayer]:
            size += CItemLayer.size_bytes()

        header = CItemHeader.from_data(self._data)
        if (header.type_id_index & 0xffff) != index:
            raise RuntimeError('index of item is not as expected')
        if (header.type_id_index >> 16) & 0xffff != self._get_typeid(item_type):
            raise RuntimeError('type_id of item is not as expected')
        if header.size != size:
            raise RuntimeError('size of item_data is not as expected')

    def _get_item(self, item_type: Type[T], index: int) -> T:
        start = self._get_type_start(item_type)
        if start is None:
            raise RuntimeError('item should not have been requested')

        self._data.seek(self._items_start + self._item_offsets[start + index])
        self._validate_item_header(index, item_type)

        if item_type in [CItemTileLayer, CItemQuadLayer, CItemSoundLayer]:
            CItemLayer.from_data(self._data)  # this has already been read

        return item_type.from_data(self._data)

    def get_version(self):
        item = self._get_item(CItemVersion, 0)

        if item.version != 1:
            raise RuntimeError('unsupported ItemVersion version')

        return ItemVersion(version=item.version)

    def get_info(self):
        item = self._get_item(CItemInfo, 0)

        if item.version != 1:
            raise RuntimeError('unsupported ItemInfo version')

        author = self._get_data_str(item.author_ptr)
        mapversion = self._get_data_str(item.map_version_ptr)
        credits = self._get_data_str(item.credits_ptr)
        license = self._get_data_str(item.license_ptr)
        settings: list[str] = self._get_data_str_list(item.settings_ptr)

        return ItemInfo(
            author=author,
            mapversion=mapversion,
            credits=credits,
            license=license,
            settings=settings
        )

    def _get_image(self, index: int):
        # check for optional pointers
        if index < 0:
            return None

        if index in self._image_cache:
            return self._image_cache[index]

        item = self._get_item(CItemImage, index)

        if item.version != 1:
            raise RuntimeError('unexpected tilelayer version')

        name = self._get_data_str(item.name_ptr)

        if item.external:
            img_item = ItemImageExternal(name=name)
        else:
            loaded_img: Image.Image = Image.frombytes(  # type: ignore
                'RGBA',
                (item.width, item.height),
                self._get_data(item.data_ptr)
            )
            img_item = ItemImageInternal(image=loaded_img, name=name)

        self._image_cache[index] = img_item
        return img_item

    def _get_envelope(self, index: int):
        pass

    def _add_tile_layer(self, index: int, detail: bool):
        item = self._get_item(CItemTileLayer, index)

        if item.version != 3:
            raise RuntimeError('unexpected tilelayer version')

        # read flags
        flags = item.flags
        is_game = TileLayerFlags.GAME & flags > 0
        is_tele = TileLayerFlags.TELE & flags > 0
        is_speedup = TileLayerFlags.SPEEDUP & flags > 0
        is_front = TileLayerFlags.FRONT & flags > 0
        is_switch = TileLayerFlags.SWITCH & flags > 0
        is_tune = TileLayerFlags.TUNE & flags > 0

        # set managertype and data_ptr
        manager_type = VanillaTileManager
        data_ptr = item.data_ptr
        if is_tele:
            manager_type = TeleTileManager
            data_ptr = item.data_tele_ptr
        elif is_speedup:
            manager_type = SpeedupTileManager
            data_ptr = item.data_speedup_ptr
        elif is_front:
            data_ptr = item.data_front_ptr
        elif is_switch:
            manager_type = SwitchTileManager
            data_ptr = item.data_switch_ptr
        elif is_tune:
            manager_type = TuneTileManager
            data_ptr = item.data_tune_ptr

        # find references
        env_ref: Optional[ItemEnvelope] = self._get_envelope(item.color_envelope_ref)
        image_ref: Optional[ItemImage] = self._get_image(item.image_ref)

        tile_manager = manager_type(
            item.width,
            item.height,
            data=self._get_data(data_ptr)
        )

        layer_item = ItemTileLayer(
            tiles=tile_manager,
            color_envelope_ref=env_ref,
            image_ref=image_ref,
            color_envelope_offset=item.color_envelope_offset,
            color=item.color.as_tuple(),
            detail=detail,
            name=item.name
        )

        if is_game:
            self.game_layer = layer_item  # type: ignore
        elif is_tele:
            self.tele_layer = layer_item  # type: ignore
        elif is_speedup:
            self.speedup_layer = layer_item  # type: ignore
        elif is_front:
            self.front_layer = layer_item  # type: ignore
        elif is_switch:
            self.switch_layer = layer_item  # type: ignore
        elif is_tune:
            self.tune_layer = layer_item  # type: ignore

        self._layer_cache[index] = layer_item
        return layer_item

    def _add_quad_layer(self, index: int, detail: bool):
        # if item_data.version.value != 3:
        #     raise RuntimeError('unexpected tilelayer version')
        pass

    def _add_sound_layer(self, index: int, detail: bool):
        # if item_data.version.value != 3:
        #     raise RuntimeError('unexpected tilelayer version')
        pass

    def _get_layer(self, index: int):
        # check for optional pointers
        if index < 0:
            return None

        if index in self._layer_cache:
            return self._layer_cache[index]

        item = self._get_item(CItemLayer, index)

        detail = LayerFlags.DETAIL & item.flags > 0

        if item.type in [LayerType.SOUNDS, LayerType.SOUNDS_DEPCRECATED]:
            return self._add_sound_layer(index, detail)
        elif item.type == LayerType.QUADS:
            return self._add_quad_layer(index, detail)
        else:
            return self._add_tile_layer(index, detail)

    def _get_groups_generator(self):
        for i in range(self._get_num_items(CItemGroup)):
            item = self._get_item(CItemGroup, i)

            if item.version != 3:
                raise RuntimeError('unexpected tilelayer version')

            layer_refs: list[ItemLayer] = []
            for k in range(item.num_layers):
                ref = self._get_layer(item.start_layer + k)
                if ref:
                    layer_refs.append(ref)
                # TODO: enable when all layers have been implemented
                # else:
                #     raise RuntimeError('')
            if len(layer_refs) == 0:
                continue  # TODO: remove when all layers have been implemented

            yield ItemGroup(
                layers=layer_refs,
                x_offset=item.x_offset,
                y_offset=item.y_offset,
                x_parallax=item.x_parallax,
                y_parallax=item.y_parallax,
                clipping=item.clipping > 0,
                clip_x=item.clip_x,
                clip_y=item.clip_y,
                clip_width=item.clip_width,
                clip_height=item.clip_height,
                name=item.name
            )

    def get_groups(self):
        return list(self._get_groups_generator())
