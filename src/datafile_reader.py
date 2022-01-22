from stringfile import StringFile
from structs import c_int32
from map_structs import CVersionHeader, CHeaderV4, CItemType, CItemVersion
from items import ItemVersion
from constants import EnumItemType


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

        self._item_offsets = [c_int32.from_data(self._data) for _ in range(self._header.num_items.value)]
        self._data_offsets = [c_int32.from_data(self._data) for _ in range(self._header.num_data.value)]
        self._data_sizes = [c_int32.from_data(self._data) for _ in range(self._header.num_data.value)]

        self._items_start = self._data.tell()

        self._calc_data_start()

    def _calc_data_start(self):
        self._data_start = self._header.num_item_types.value * CItemType.size_bytes()
        self._data_start += (self._header.num_items.value + 2 * self._header.num_data.value) * c_int32.size_bytes()
        self._data_start += self._header.item_size.value
        self._data_start += CVersionHeader.size_bytes() + CHeaderV4.size_bytes()

    def _get_item(self, type_id: EnumItemType, index: int):
        pass

    @property
    def item_version(self):
        header, item = self._get_item(EnumItemType.VERSION, 0)
        if not isinstance(item, CItemVersion):
            raise RuntimeError('unexpected item returned')
        return ItemVersion(item.version.value), 0
