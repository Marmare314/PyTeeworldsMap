# from stringfile import StringFile  # TODO: testing
from structs import c_rawstr4, c_int32, c_struct


class VersionHeader(c_struct):
    magic: c_rawstr4
    version: c_int32


class HeaderV4(c_struct):
    size: c_int32
    swaplen: c_int32
    num_item_types: c_int32
    num_items: c_int32
    num_data: c_int32
    item_size: c_int32
    data_size: c_int32


class ItemType(c_struct):
    type_id: c_int32
    start: c_int32
    num: c_int32


# s = StringFile('test_maps/HeyTux2.map', 'R')
# ver_header = VersionHeader.from_data(s)
# header = HeaderV4.from_data(s)
# item_types = [ItemType.from_data(s) for _ in range(header.num_item_types.value)]
# print(item_types)
