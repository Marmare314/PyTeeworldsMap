# pyright: reportPrivateUsage=false

from collections import defaultdict
from constants import EnumItemType
from map_structs import CHeaderV4, CItemGroup, CItemHeader, CItemImage, CItemInfo, CItemType, CItemVersion, CVersionHeader
from stringfile import StringFile
from structs import c_intstr3, c_rawstr4, c_int32, c_struct, c_type
from items import Item, ItemGroup, ItemImage, ItemInfo, ItemLayer, ItemVersion
import zlib


class DataFileWriter:
    def __init__(self):
        self._data_file = StringFile(b'')

        self._item_types: defaultdict[int, int] = defaultdict(int)
        self._items: defaultdict[int, list[c_type | c_struct]] = defaultdict(list)

        self._data = StringFile(b'')
        self._data_offsets: list[int] = []
        self._data_sizes: list[int] = []

    def register_item(self, item: Item):
        if isinstance(item, ItemVersion):
            self._register_item_version(item)
        elif isinstance(item, ItemInfo):
            self._register_item_info(item)
        elif isinstance(item, ItemImage):
            self._register_item_image(item)
        elif isinstance(item, ItemLayer):
            pass
        elif isinstance(item, ItemGroup):
            pass
        else:
            raise NotImplementedError()

    def _register_item_version(self, item: ItemVersion):
        c_item = CItemVersion()
        c_item.version = c_int32(item.version)

        self._item_types[EnumItemType.VERSION] += 1
        self._items[EnumItemType.VERSION].append(c_item)

    def _register_item_info(self, item: ItemInfo):
        author_ptr = -1
        mapversion_ptr = -1
        credits_ptr = -1
        license_ptr = -1
        settings_ptr = -1

        if item.author:
            author_ptr = self._register_data_str(item.author)
        if item.mapversion:
            mapversion_ptr = self._register_data_str(item.mapversion)
        if item.credits:
            credits_ptr = self._register_data_str(item.credits)
        if item.license:
            license_ptr = self._register_data_str(item.license)
        if item.settings:
            settings_ptr = self._register_data_str_list(item.settings)

        c_item = CItemInfo()
        c_item.version = c_int32(1)
        c_item.author_ptr = c_int32(author_ptr)
        c_item.map_version_ptr = c_int32(mapversion_ptr)
        c_item.credits_ptr = c_int32(credits_ptr)
        c_item.license_ptr = c_int32(license_ptr)
        c_item.settings_ptr = c_int32(settings_ptr)

        self._item_types[EnumItemType.INFO] += 1
        self._items[EnumItemType.INFO].append(c_item)

    def _register_item_image(self, item: ItemImage):
        name_ptr = self._register_data_str(item.name)
        data_ptr = -1
        if not item.external:
            data_ptr = self._register_data(item.image.tobytes())  # type: ignore

        c_item = CItemImage()
        c_item.version = c_int32(1)
        c_item.width = c_int32(item.image.width)
        c_item.height = c_int32(item.image.height)
        c_item.external = c_int32(item.external)
        c_item.name_ptr = c_int32(name_ptr)
        c_item.data_ptr = c_int32(data_ptr)

        self._item_types[EnumItemType.IMAGE] += 1
        self._items[EnumItemType.IMAGE].append(c_item)

    def _register_item_layer(self, item: ItemLayer):
        pass

    def _register_item_group(self, item: ItemGroup):
        c_item = CItemGroup()
        c_item.version = c_int32(3)
        c_item.x_offset = c_int32(item.x_offset)
        c_item.y_offset = c_int32(item.y_offset)
        c_item.x_parallax = c_int32(item.x_parallax)
        c_item.y_parallax = c_int32(item.y_parallax)
        c_item.start_layer = c_int32(item.layers[0]._item_id)
        c_item.num_layers = c_int32(len(item.layers))

        c_item.clipping = c_int32(item.clipping)
        c_item.clip_x = c_int32(item.clip_x)
        c_item.clip_y = c_int32(item.clip_y)
        c_item.clip_width = c_int32(item.clip_width)
        c_item.clip_height = c_int32(item.clip_height)

        c_item.name = c_intstr3(item.name)

        self._item_types[EnumItemType.GROUP] += 1
        self._items[EnumItemType.GROUP].append(c_item)

    def _register_data_str_list(self, data: list[str]):
        byte_data = b''
        for s in data:
            byte_data += s.encode('utf8') + b'\0'
        return self._register_data(byte_data)

    def _register_data_str(self, data: str):
        return self._register_data(data.encode('utf8') + b'\0')

    def _register_data(self, data: bytes):
        self._data_offsets.append(len(self._data))
        self._data_sizes.append(len(data))

        compressed_data = zlib.compress(data)
        self._data.append(compressed_data)

        return len(self._data_offsets) - 1

    def _write_ver_header(self):
        c_item = CVersionHeader()
        c_item.magic = c_rawstr4('DATA')
        c_item.version = c_int32(4)

        self._data_file.append(c_item.to_bytes())

    def _get_item_size(self):
        item_size = 0
        for type_id in sorted(self._items):
            for item in self._items[type_id]:
                item_size += item.size_bytes() + CItemHeader.size_bytes()
        return item_size

    def _get_num_items(self):
        num_items = 0
        for type_id in sorted(self._items):
            num_items += len(self._items[type_id])
        return num_items

    def _get_swaplen(self):
        swaplen = 5 * c_int32.size_bytes()  # remaining header
        swaplen += len(self._item_types) * CItemType.size_bytes()
        swaplen += len(self._get_item_offsets()) * c_int32.size_bytes()
        swaplen += 2 * len(self._data_offsets) * c_int32.size_bytes()
        swaplen += self._get_item_size()
        return swaplen

    def _get_size(self):
        return self._get_swaplen() + len(self._data)

    def _write_header(self):
        c_item = CHeaderV4()
        c_item.size = c_int32(self._get_size())
        c_item.swaplen = c_int32(self._get_swaplen())
        c_item.num_item_types = c_int32(len(self._item_types))
        c_item.num_items = c_int32(self._get_num_items())
        c_item.num_data = c_int32(len(self._data_offsets))
        c_item.item_size = c_int32(self._get_item_size())
        c_item.data_size = c_int32(len(self._data))

        self._data_file.append(c_item.to_bytes())

    def _write_item_types(self):
        start = 0
        for type_id in sorted(self._item_types):
            num = len(self._items[type_id])

            c_item = CItemType()
            c_item.type_id = c_int32(type_id)
            c_item.start = c_int32(start)
            c_item.num = c_int32(num)

            self._data_file.append(c_item.to_bytes())

            start += num

    def _get_item_offsets(self):
        offsets: list[int] = []
        next_offset = 0
        for type_id in sorted(self._items):
            for item in self._items[type_id]:
                offsets.append(next_offset)
                next_offset += item.size_bytes() + CItemHeader.size_bytes()
        return offsets

    def _write_size_indicators(self):
        for offset in self._get_item_offsets():
            self._data_file.append(c_int32(offset).to_bytes())

        for offset in self._data_offsets:
            self._data_file.append(c_int32(offset).to_bytes())

        for size in self._data_sizes:
            self._data_file.append(c_int32(size).to_bytes())

    def _write_items(self):
        for type_id in sorted(self._items):
            for index, item in enumerate(self._items[type_id]):
                item_bytes = item.to_bytes()

                combined = index | (type_id << 16)

                c_item = CItemHeader()
                c_item.type_id_index = c_int32(combined)
                c_item.size = c_int32(len(item_bytes))

                self._data_file.append(c_item.to_bytes())
                self._data_file.append(item_bytes)

    def write(self, path: str):
        self._write_ver_header()
        self._write_header()
        self._write_item_types()
        self._write_size_indicators()
        self._write_items()
        self._data_file.append(self._data.read_all())

        return self._data_file.read_all()
        # with open(path, 'wb') as file:
        #     file.write(self._data_file.read_all())
