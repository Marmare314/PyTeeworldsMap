from stringfile import StringFile
from structs import c_int32
from map_structs import CVersionHeader, CHeaderV4, CItemType, CItemVersion, CItemHeader, CItemInfo
from items import ItemVersion, ItemInfo
from constants import EnumItemType
import zlib


class DataFileReader:
    def __init__(self, path: str):
        self._data = StringFile(path, 'R')

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

    def _get_item(self, type_id: EnumItemType, index: int):
        self._data.seek(self._items_start + self._item_offsets[self._get_type_start(type_id) + index])

        # TODO: check that sizes match
        if type_id == EnumItemType.VERSION:
            return CItemHeader.from_data(self._data), CItemVersion.from_data(self._data)
        else:
            return 1, 2
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
