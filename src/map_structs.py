from structs import c_rawstr4, c_int32, c_struct, c_uint16


class CVersionHeader(c_struct):
    magic: c_rawstr4
    version: c_int32


class CHeaderV4(c_struct):
    size: c_int32
    swaplen: c_int32
    num_item_types: c_int32
    num_items: c_int32
    num_data: c_int32
    item_size: c_int32
    data_size: c_int32


class CItemType(c_struct):
    type_id: c_int32
    start: c_int32
    num: c_int32


class CItemHeader(c_struct):
    type_id: c_uint16
    index: c_uint16
    size: c_int32


class CItemVersion(c_struct):
    version: c_int32
