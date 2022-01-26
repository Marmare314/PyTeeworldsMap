from structs import c_intstr3, c_rawstr4, c_int32, c_struct, c_i32_color


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
    type_id_index: c_int32
    size: c_int32


class CItemVersion(c_struct):
    version: c_int32


class CItemInfo(c_struct):
    version: c_int32
    author_ptr: c_int32
    map_version_ptr: c_int32
    credits_ptr: c_int32
    license_ptr: c_int32
    settings_ptr: c_int32


class CItemImage(c_struct):
    version: c_int32
    width: c_int32
    height: c_int32
    external: c_int32
    name_ptr: c_int32
    data_ptr: c_int32
    # variant: c_int32  # ver2 extension (vanilla)


class CItemEnvelope(c_struct):
    pass


class CItemEnvPointSound(c_struct):
    time: c_int32
    curve_type: c_int32
    volume: c_int32
    _unused_1: c_int32
    _unused_2: c_int32
    _unused_3: c_int32


class CItemEnvPointPosition(c_struct):
    time: c_int32
    curve_type: c_int32
    x: c_int32
    y: c_int32
    rotation: c_int32
    _unused: c_int32


class CItemEnvPointColor(c_struct):
    time: c_int32
    curve_type: c_int32
    color: c_i32_color


class CItemGroup(c_struct):
    version: c_int32
    x_offset: c_int32
    y_offset: c_int32
    x_parallax: c_int32
    y_parallax: c_int32
    start_layer: c_int32
    num_layers: c_int32

    # ver2 extension
    clipping: c_int32
    clip_x: c_int32
    clip_y: c_int32
    clip_width: c_int32
    clip_height: c_int32

    # ver3 extension
    name: c_intstr3


class CItemLayer(c_struct):
    version: c_int32
    type: c_int32
    flags: c_int32


class CItemTileLayer(c_struct):
    version: c_int32
    width: c_int32
    height: c_int32
    flags: c_int32
    color: c_i32_color
    color_envelope_ref: c_int32
    color_envelope_offset: c_int32
    image_ref: c_int32
    data_ptr: c_int32

    # ver3 extension
    name: c_intstr3

    # ddnet extension
    data_tele_ptr: c_int32
    data_speedup_ptr: c_int32
    data_front_ptr: c_int32
    data_switch_ptr: c_int32
    data_tune_ptr: c_int32


class CItemQuadLayer(c_struct):
    pass


class CQuad(c_struct):
    pass


class CItemSoundLayer(c_struct):
    pass


class CSoundShape(c_struct):
    pass


class CSoundSource(c_struct):
    pass


class CItemSound(c_struct):
    pass
