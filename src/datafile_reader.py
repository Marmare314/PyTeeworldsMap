# pyright: reportPrivateUsage=false

from stringfile import StringFile
from structs import c_int32
from map_structs import CItemGroup, CItemLayer, CItemQuadLayer, CItemSoundLayer, CItemTileLayer, CVersionHeader, CHeaderV4, CItemType, CItemVersion, CItemHeader, CItemInfo, CItemImage
from items import ItemEnvelope, ItemGroup, ItemImage, ItemLayer, ItemVersion, ItemInfo, SpeedupTileLayer, SwitchTileLayer, TeleTileLayer, TuneTileLayer, VanillaTileLayer
from constants import EnumItemType, EnumLayerFlags, EnumLayerType, EnumTileLayerFlags
import zlib
from PIL import Image
from typing import Optional, TypeVar

from tilemanager import SpeedupTileManager, SwitchTileManager, TeleTileManager, TuneTileManager, VanillaTileManager


T = TypeVar('T')


class DataFileReader:
    def __init__(self, path: str):
        with open(path, 'rb') as file:
            self._data = StringFile(file.read())

        self._ver_header = CVersionHeader.from_data(self._data)
        if self._ver_header.magic.value not in ['DATA', 'ATAD']:
            raise RuntimeError('wrong magic bytes')
        if self._ver_header.version.value != 4:
            raise RuntimeError('only version 4 is supported')

        self._header = CHeaderV4.from_data(self._data)

        self._item_types = [CItemType.from_data(self._data) for _ in range(self._header.num_item_types.value)]

        self._item_offsets = [c_int32.from_data(self._data).value for _ in range(self._header.num_items.value)]
        self._data_offsets = [c_int32.from_data(self._data).value for _ in range(self._header.num_data.value)]
        self._data_sizes = [c_int32.from_data(self._data).value for _ in range(self._header.num_data.value)]

        self._items_start = self._data.tell()

        self._calc_data_start()

    def _calc_data_start(self):
        self._data_start = self._header.num_item_types.value * CItemType.size_bytes()
        self._data_start += (self._header.num_items.value + 2 * self._header.num_data.value) * c_int32.size_bytes()
        self._data_start += self._header.item_size.value
        self._data_start += CVersionHeader.size_bytes() + CHeaderV4.size_bytes()

    def _get_data(self, data_ptr: int):
        offset_begin = self._data_offsets[data_ptr]
        offset_end = self._header.size.value
        if data_ptr + 1 < len(self._data_offsets):
            offset_end = self._data_offsets[data_ptr + 1]
        num_bytes = offset_end - offset_begin

        self._data.seek(self._data_start + offset_begin)
        return zlib.decompress(self._data.read(num_bytes))

    def _get_data_str(self, data_ptr: int):
        return self._get_data(data_ptr)[:-1].decode('utf8')

    def _get_data_str_list(self, data_ptr: int):
        return ['']

    def _get_type_start(self, type_id: EnumItemType):
        for item_type in self._item_types:
            if item_type.type_id.value == type_id:
                return item_type.start.value
        raise RuntimeError('type_id not found')

    def _get_num_items(self, type_id: EnumItemType):
        for item_type in self._item_types:
            if item_type.type_id.value == type_id:
                return item_type.num.value
        raise RuntimeError('type_id not found')

    def _get_item(self, type_id: EnumItemType, index: int):
        self._data.seek(self._items_start + self._item_offsets[self._get_type_start(type_id) + index])

        header = CItemHeader.from_data(self._data)
        assert header.type_id_index.value & 0xffff == index
        assert (header.type_id_index.value >> 16) & 0xffff == type_id

        if type_id == EnumItemType.VERSION:
            assert header.size.value == CItemVersion.size_bytes()
            return CItemVersion.from_data(self._data)
        elif type_id == EnumItemType.INFO:
            assert header.size.value == CItemInfo.size_bytes()
            return CItemInfo.from_data(self._data)
        elif type_id == EnumItemType.IMAGE:
            assert header.size.value == CItemImage.size_bytes()
            return CItemImage.from_data(self._data)
        elif type_id == EnumItemType.LAYER:
            layer_header = CItemLayer.from_data(self._data)
            if layer_header.type.value == EnumLayerType.TILES:
                assert header.size.value == CItemLayer.size_bytes() + CItemTileLayer.size_bytes()
                return layer_header, CItemTileLayer.from_data(self._data)
            elif layer_header.type.value == EnumLayerType.QUADS:
                # TODO: enable when implemented
                # assert header.size.value == CItemLayer.size_bytes() + CItemQuadLayer.size_bytes()
                return layer_header, CItemQuadLayer.from_data(self._data)
            elif layer_header.type.value == EnumLayerType.SOUNDS:
                assert header.size.value == CItemLayer.size_bytes() + CItemSoundLayer.size_bytes()
                return layer_header, CItemSoundLayer.from_data(self._data)
            else:
                raise RuntimeError('layer type not recognized')
        elif type_id == EnumItemType.GROUP:
            assert header.size.value == CItemGroup.size_bytes()
            return CItemGroup.from_data(self._data)
        raise RuntimeError('type_id not known')

    @staticmethod
    def _set_id(item: T, id: int) -> T:
        item._item_id = id  # type: ignore
        return item

    @property
    def item_version(self):
        item = self._get_item(EnumItemType.VERSION, 0)
        if not isinstance(item, CItemVersion):
            raise RuntimeError('unexpected item returned')

        if item.version.value != 1:
            raise RuntimeError('unsupported ItemVersion version')

        ret_item = ItemVersion(item.version.value)
        return self._set_id(ret_item, 0)

    @property
    def item_info(self):
        item = self._get_item(EnumItemType.INFO, 0)
        if not isinstance(item, CItemInfo):
            raise RuntimeError('unexpected item returned')

        if item.version.value != 1:
            raise RuntimeError('unsupported ItemInfo version')

        author = ''
        mapversion = ''
        credits = ''
        license = ''
        settings: list[str] = []

        if item.author_ptr.value > 0:
            author = self._get_data_str(item.author_ptr.value)
        if item.map_version_ptr.value > 0:
            mapversion = self._get_data_str(item.map_version_ptr.value)
        if item.credits_ptr.value > 0:
            credits = self._get_data_str(item.credits_ptr.value)
        if item.license_ptr.value > 0:
            license = self._get_data_str(item.license_ptr.value)
        if item.settings_ptr.value > 0:
            settings = self._get_data_str_list(item.settings_ptr.value)

        ret_item = ItemInfo(author, mapversion, credits, license, settings)
        return self._set_id(ret_item, 0)

    @property
    def item_images(self):
        for i in range(self._get_num_items(EnumItemType.IMAGE)):
            item = self._get_item(EnumItemType.IMAGE, i)
            if not isinstance(item, CItemImage):
                raise RuntimeError('unexpected item returned')

            if item.version.value != 1:
                raise RuntimeError('unexpected tilelayer version')

            name = ''
            if item.name_ptr.value > 0:
                name = self._get_data_str(item.name_ptr.value)

            image = ItemImage()
            if item.external.value:
                image.set_external(name)
            else:
                loaded_img: Image.Image = Image.frombytes(  # type: ignore
                    'RGBA',
                    (item.width.value, item.height.value),
                    self._get_data(item.data_ptr.value)
                )
                image.set_internal(loaded_img, name)

            yield self._set_id(image, i)

    def _get_item_tile_layer(self,
                             layer_header: CItemLayer,
                             item_data: CItemTileLayer,
                             index: int,
                             detail: bool):
        if item_data.version.value != 3:
            raise RuntimeError('unexpected tilelayer version')

        flags = item_data.flags.value
        is_game = EnumTileLayerFlags.GAME & flags > 0
        is_tele = EnumTileLayerFlags.TELE & flags > 0
        is_speedup = EnumTileLayerFlags.SPEEDUP & flags > 0
        is_front = EnumTileLayerFlags.FRONT & flags > 0
        is_switch = EnumTileLayerFlags.SWITCH & flags > 0
        is_tune = EnumTileLayerFlags.TUNE & flags > 0

        layer_type = VanillaTileLayer
        if is_tele:
            layer_type = TeleTileLayer
        elif is_speedup:
            layer_type = SpeedupTileLayer
        elif is_switch:
            layer_type = SwitchTileLayer
        elif is_tune:
            layer_type = TuneTileLayer

        env_ref: Optional[ItemEnvelope] = None
        env_ref_id = item_data.color_envelope_ref.value
        if env_ref_id > 0:
            env_ref = self._set_id(ItemEnvelope(), env_ref_id)

        image_ref: Optional[ItemImage] = None
        image_ref_id = item_data.image_ref.value
        if image_ref_id > 0:
            image_ref = self._set_id(ItemImage(), image_ref_id)

        width = item_data.width.value
        height = item_data.height.value
        layer = layer_type(
            width,
            height,
            env_ref,
            image_ref,
            item_data.color_envelope_offset.value,
            item_data.color.value,
            detail,
            is_game,
            is_tele,
            is_speedup,
            is_front,
            is_switch,
            is_tune,
            item_data.name.value
        )

        if isinstance(layer, VanillaTileLayer):
            data_ptr = item_data.data_ptr.value
            if is_front:
                data_ptr = item_data.data_front_ptr.value
            layer.tiles = VanillaTileManager(width, height, is_front | is_game, self._get_data(data_ptr))
        elif isinstance(layer, TeleTileLayer):
            data_ptr = item_data.data_tele_ptr.value
            layer.tiles = TeleTileManager(width, height, self._get_data(data_ptr))
        elif isinstance(layer, SpeedupTileLayer):
            data_ptr = item_data.data_speedup_ptr.value
            layer.tiles = SpeedupTileManager(width, height, self._get_data(data_ptr))
        elif isinstance(layer, SwitchTileLayer):
            data_ptr = item_data.data_switch_ptr.value
            layer.tiles = SwitchTileManager(width, height, self._get_data(data_ptr))
        else:
            data_ptr = item_data.data_tune_ptr.value
            layer.tiles = TuneTileManager(width, height, self._get_data(data_ptr))

        return self._set_id(layer, index)

    def _get_item_quad_layer(self,
                             layer_header: CItemLayer,
                             item_data: CItemQuadLayer,
                             index: int,
                             detail: bool):
        # if item_data.version.value != 3:
        #     raise RuntimeError('unexpected tilelayer version')
        return self._set_id(VanillaTileLayer(0, 0), index)

    def _get_item_sound_layer(self,
                              layer_header: CItemLayer,
                              item_data: CItemSoundLayer,
                              index: int,
                              detail: bool):
        # if item_data.version.value != 3:
        #     raise RuntimeError('unexpected tilelayer version')
        return self._set_id(VanillaTileLayer(0, 0), index)

    def _get_item_layer(self, index: int):
        item = self._get_item(EnumItemType.LAYER, index)
        if not isinstance(item, tuple):
            raise RuntimeError('unexpected item returned')

        detail = EnumLayerFlags.DETAIL & item[0].flags.value > 0

        if isinstance(item[1], CItemTileLayer):
            return self._get_item_tile_layer(item[0], item[1], index, detail)
        elif isinstance(item[1], CItemQuadLayer):
            return self._get_item_quad_layer(item[0], item[1], index, detail)
        else:
            return self._get_item_sound_layer(item[0], item[1], index, detail)

    @property
    def item_layers(self):
        for i in range(self._get_num_items(EnumItemType.LAYER)):
            yield self._get_item_layer(i)

    @property
    def item_groups(self):
        for i in range(self._get_num_items(EnumItemType.GROUP)):
            item = self._get_item(EnumItemType.GROUP, i)
            if not isinstance(item, CItemGroup):
                raise RuntimeError('unexpected item returned')

            if item.version.value != 3:
                raise RuntimeError('unexpected tilelayer version')

            layer_refs: list[ItemLayer] = []
            for k in range(item.num_layers.value):
                ref = self._set_id(ItemLayer(), item.start_layer.value + k)
                layer_refs.append(ref)

            yield self._set_id(ItemGroup(
                layer_refs,
                item.x_offset.value,
                item.y_offset.value,
                item.x_parallax.value,
                item.y_parallax.value,
                item.clipping.value > 0,
                item.clip_x.value,
                item.clip_y.value,
                item.clip_width.value,
                item.clip_height.value,
                item.name.value
            ), i)
