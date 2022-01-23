from stringfile import StringFile
from structs import c_int32
from map_structs import CItemGroup, CItemLayer, CItemQuadLayer, CItemSoundLayer, CItemTileLayer, CVersionHeader, CHeaderV4, CItemType, CItemVersion, CItemHeader, CItemInfo, CItemImage
from items import ItemGroup, ItemImage, ItemVersion, ItemInfo, SpeedupTileLayer, SwitchTileLayer, TeleTileLayer, TuneTileLayer, VanillaTileLayer
from constants import EnumItemType, EnumLayerFlags, EnumLayerType, EnumTileLayerFlags
import zlib
from PIL import Image

from tilemanager import SpeedupTileManager, SwitchTileManager, TeleTileManager, TuneTileManager, VanillaTileManager


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
        pass

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

        # TODO: check that sizes match
        if type_id == EnumItemType.VERSION:
            return CItemHeader.from_data(self._data), CItemVersion.from_data(self._data)
        elif type_id == EnumItemType.INFO:
            return CItemHeader.from_data(self._data), CItemInfo.from_data(self._data)
        elif type_id == EnumItemType.IMAGE:
            return CItemHeader.from_data(self._data), CItemImage.from_data(self._data)
        elif type_id == EnumItemType.LAYER:
            header = CItemHeader.from_data(self._data)
            layer_header = CItemLayer.from_data(self._data)
            if layer_header.type.value == EnumLayerType.TILES:
                return header, (layer_header, CItemTileLayer.from_data(self._data))
            elif layer_header.type.value == EnumLayerType.QUADS:
                return header, (layer_header, CItemQuadLayer.from_data(self._data))
            elif layer_header.type.value == EnumLayerType.SOUNDS:
                return header, (layer_header, CItemSoundLayer.from_data(self._data))
            else:
                raise RuntimeError('layer type not recognized')
        elif type_id == EnumItemType.GROUP:
            return CItemHeader.from_data(self._data), CItemGroup.from_data(self._data)
        raise RuntimeError('type_id not known')

    @property
    def item_version(self):
        _, item = self._get_item(EnumItemType.VERSION, 0)
        if not isinstance(item, CItemVersion):
            raise RuntimeError('unexpected item returned')

        # TODO: check version

        return ItemVersion(item.version.value), 0

    @property
    def item_info(self):
        _, item = self._get_item(EnumItemType.INFO, 0)
        if not isinstance(item, CItemInfo):
            raise RuntimeError('unexpected item returned')

        # TODO: check version

        author = ''
        mapversion = ''
        credits = ''
        license = ''
        settings: list[str] = []

        if item.author_ptr.value > 0:
            author = self._get_data_str(item.author_ptr.value)

        # TODO: check the rest

        return ItemInfo(author, mapversion, credits, license, settings), 0

    @property
    def item_images(self):
        for i in range(self._get_num_items(EnumItemType.IMAGE)):
            _, item = self._get_item(EnumItemType.IMAGE, i)
            if not isinstance(item, CItemImage):
                raise RuntimeError('unexpected item returned')

            # TODO: check version

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

            yield image, i

    def _get_item_layer(self, index: int):
        _, item = self._get_item(EnumItemType.LAYER, index)
        if not isinstance(item, tuple):
            raise RuntimeError('unexpected item returned')
        if not isinstance(item[0], CItemLayer):
            raise RuntimeError('unexpected item returned')

        # TODO: check version

        detail = EnumLayerFlags.DETAIL & item[0].flags.value > 0

        if isinstance(item[1], CItemTileLayer):
            flags = item[1].flags.value
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

            width = item[1].width.value
            height = item[1].height.value
            layer = layer_type(
                width,
                height,
                item[1].color_envelope_ref.value,
                item[1].image_ref.value,
                item[1].color_envelope_offset.value,
                item[1].color.value,
                detail,
                is_game,
                is_tele,
                is_speedup,
                is_front,
                is_switch,
                is_tune,
                item[1].name.value
            )

            if isinstance(layer, VanillaTileLayer):
                data_ptr = item[1].data_ptr.value
                if is_front:
                    data_ptr = item[1].data_front_ptr.value
                layer.tiles = VanillaTileManager(width, height, is_front | is_game, self._get_data(data_ptr))
            elif isinstance(layer, TeleTileLayer):
                data_ptr = item[1].data_tele_ptr.value
                layer.tiles = TeleTileManager(width, height, self._get_data(data_ptr))
            elif isinstance(layer, SpeedupTileLayer):
                data_ptr = item[1].data_speedup_ptr.value
                layer.tiles = SpeedupTileManager(width, height, self._get_data(data_ptr))
            elif isinstance(layer, SwitchTileLayer):
                data_ptr = item[1].data_switch_ptr.value
                layer.tiles = SwitchTileManager(width, height, self._get_data(data_ptr))
            else:
                data_ptr = item[1].data_tune_ptr.value
                layer.tiles = TuneTileManager(width, height, self._get_data(data_ptr))

            return layer, index
        elif isinstance(item[1], CItemQuadLayer):
            return VanillaTileLayer(1, 1), 0
        else:
            raise NotImplementedError()

    @property
    def item_layers(self):
        for i in range(self._get_num_items(EnumItemType.LAYER)):
            yield self._get_item_layer(i)

    @property
    def item_groups(self):
        for i in range(self._get_num_items(EnumItemType.GROUP)):
            _, item = self._get_item(EnumItemType.GROUP, i)
            if not isinstance(item, CItemGroup):
                raise RuntimeError('unexpected item returned')

            # TODO: check version

            yield ItemGroup(
                [item.start_layer.value + i for i in range(item.num_layers.value)],
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
            ), i
