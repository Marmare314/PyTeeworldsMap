import zlib

from utils import ItemType, ints_to_string


# TODO: introduce enums
class DataFileReader:
    def __init__(self, path: str):
        # open file and store bytes
        with open(path, 'rb') as file:
            self._content = file.read()

        # init reading position
        self._pointer = 0
        self._mark_pos = 0

        # validate file format
        magic = self._read(4)
        if not (magic == b'DATA' or magic == b'ATAD'):
            raise ValueError('DataFileReader: magic string not correct')

        self._version = self._read_int(4)
        if not self._version == 4:
            raise ValueError('DataFileReader: version 4 expected')

        # read header
        self._size = self._read_int(4)
        self._swaplen = self._read_int(4)
        self._num_item_types = self._read_int(4)
        self._num_items = self._read_int(4)
        self._num_data = self._read_int(4)
        self._item_size = self._read_int(4)
        self._data_size_unc = self._read_int(4)

        # read itemtypes
        self._item_types = []
        for _ in range(self._num_item_types):
            self._item_types.append({
                'type_id': self._read_int(4),
                'start': self._read_int(4),
                'num': self._read_int(4)
            })

        # read offsets
        self._item_offsets = [self._read_int(4) for _ in range(self._num_items)]
        self._data_offsets = [self._read_int(4) for _ in range(self._num_data)]
        self._data_sizes = [self._read_int(4) for _ in range(self._num_data)]

        # save items start
        self._items_start = self._pointer

        # calculate data section start
        self._data_start = self._num_item_types * 12
        self._data_start += (self._num_items + self._num_data) * 4
        self._data_start += self._num_data * 4  # ! only version 4
        self._data_start += self._item_size
        self._data_start += 36

    def _read(self, num_bytes: int):
        value = self._content[self._pointer:self._pointer + num_bytes]
        self._pointer += num_bytes
        return value

    def _read_int(self, num_bytes: int, signed: bool = True):
        return int.from_bytes(self._read(num_bytes), byteorder='little', signed=signed)

    def _read_istr(self, num_ints: int):
        return ints_to_string([self._read_int(4) for _ in range(num_ints)])

    def _seek(self, pos: int):
        self._pointer = pos

    def _mark(self):
        self._mark_pos = self._pointer

    def _num_bytes_read(self):
        return self._pointer - self._mark_pos

    def get_num_items(self, type_id: int):
        for item_type in self._item_types:
            if item_type['type_id'] == type_id:
                return item_type['num']

    def get_item(self, type_id: int, index: int):
        num_prev_items = 0
        for item_type in self._item_types:
            if item_type['type_id'] == type_id:
                if index < 0 or index >= item_type['num']:
                    raise ValueError('Index out of range')

                self._seek(self._items_start + self._item_offsets[num_prev_items + index])

                # just make sure the ids and indices match
                if not (index == self._read_int(2, False) and type_id == self._read_int(2, False)):
                    raise ValueError()

                size = self._read_int(4)

                if type_id == 0:
                    return self._read_item_version(size)
                elif type_id == 1:
                    return self._read_item_info(size)
                elif type_id == 2:
                    return self._read_item_image(size)
                elif type_id == 3:
                    return self._read_item_envelope(size)
                elif type_id == 4:
                    return self._read_item_group(size)
                elif type_id == 5:
                    return self._read_item_layer(size)
                elif type_id == 6:
                    raise ValueError('use get_envpoint instead')
                else:
                    raise ValueError('unrecognized type_id')

            else:
                num_prev_items += item_type['num']

        raise ValueError('Item not found')

    def get_envpoint(self, channel: int, start_point: int, num_points: int):
        # TODO: add bezier support
        num_prev_items = 0
        for item_type in self._item_types:
            if item_type['type_id'] == 6:
                envpoint_begin = self._items_start + self._item_offsets[num_prev_items]

                self._seek(envpoint_begin + start_point * 24)  # 24 -> assuming version <= 2

                envpoints: list[dict[str, Union[int, list[int]]]] = []
                for _ in range(num_points):
                    if channel == 1:
                        envpoints.append({
                            'time': self._read_int(4),
                            'curve_type': self._read_int(4),
                            'volume': self._read_int(4)
                        })
                        self._read_int(12)  # skip last bytes
                    elif channel == 3:
                        envpoints.append({
                            'time': self._read_int(4),
                            'curve_type': self._read_int(4),
                            'x': self._read_int(4),
                            'y': self._read_int(4),
                            'rotation': self._read_int(4)
                        })
                        self._read_int(4)  # skip last bytes
                    elif channel == 4:
                        envpoints.append({
                            'time': self._read_int(4),
                            'curve_type': self._read_int(4),
                            'color': [self._read_int(4) for _ in range(4)]
                        })
                    else:
                        raise ValueError('unexpected channel number')

                return envpoints

            else:
                num_prev_items += item_type['num']

        raise ValueError('No envpoints found')

    def get_data(self, data_ptr: int):
        offset = self._data_offsets[data_ptr]
        next_offset = self._data_offsets[data_ptr + 1] if data_ptr + 1 < len(self._data_offsets) else self._size
        return zlib.decompress(self._content[self._data_start + offset:self._data_start + next_offset])

    def get_data_str(self, data_ptr: int):
        return self.get_data(data_ptr)[:-1].decode('ascii')

    def _read_item_version(self, size: int):
        value = {
            'version': self._read_int(4)
        }

        # TODO: refactor this
        if not size == 4:
            raise ValueError()

        if not value['version'] == 1:
            raise ValueError()

        return value

    def _read_item_info(self, size: int):
        value = {
            'version': self._read_int(4),
            'author_ptr': self._read_int(4),
            'version_ptr': self._read_int(4),
            'credits_ptr': self._read_int(4),
            'license_ptr': self._read_int(4),
            'settings_ptr': self._read_int(4)
        }

        if not size == 24:
            raise ValueError()

        if not value['version'] == 1:
            raise ValueError()

        return value

    def _read_item_image(self, size: int):
        value = {
            'version': self._read_int(4),
            'width': self._read_int(4),
            'height': self._read_int(4),
            'external': self._read_int(4),
            'name_ptr': self._read_int(4),
            'data_ptr': self._read_int(4)
        }

        if not size == 24:
            raise ValueError()

        if not value['version'] == 1:
            raise ValueError()

        return value

    def _read_item_envelope(self, size: int):
        value = {
            'version': self._read_int(4),
            'channels': self._read_int(4),
            'start_point': self._read_int(4),
            'num_points': self._read_int(4),
            'name': self._read_istr(8),
            'synchronized': self._read_int(4),
        }

        if not size == 52:
            raise ValueError()

        if not value['version'] == 2:
            raise ValueError()

        return value

    def _read_item_group(self, size: int):
        value = {
            'version': self._read_int(4),
            'x_offset': self._read_int(4),
            'y_offset': self._read_int(4),
            'x_parallax': self._read_int(4),
            'y_parallax': self._read_int(4),
            'start_layer': self._read_int(4),
            'num_layers': self._read_int(4),
            'clipping': self._read_int(4),
            'clip_x': self._read_int(4),
            'clip_y': self._read_int(4),
            'clip_width': self._read_int(4),
            'clip_height': self._read_int(4),
            'name': self._read_istr(3)
        }

        if not size == 60:
            raise ValueError()

        if not value['version'] == 3:
            raise ValueError()

        return value

    def _read_item_layer(self, size: int):
        value: dict[str, Union[int, dict[str, Union[int, bytes, list[int]]]]] = {
            'version': self._read_int(4),
            'type': self._read_int(4),
            'flags': self._read_int(4)
        }

        if value['type'] == 2:  # tile
            value['data'] = self._read_item_layer_tile(size - 12)
        elif value['type'] == 3:  # quad
            value['data'] = self._read_item_layer_quad(size - 12)
        elif value['type'] == 9:  # deprecated sound
            value['data'] = self._read_item_layer_sound(size - 12, 1)
        elif value['type'] == 10:  # sound
            value['data'] = self._read_item_layer_sound(size - 12, 0)
        else:
            raise ValueError(f'ItemLayer type {value["type"]} not known')

        return value

    def _read_item_layer_tile(self, size: int):
        value = {
            'version': self._read_int(4),
            'width': self._read_int(4),
            'height': self._read_int(4),
            'flags': self._read_int(4),
            'color': [self._read_int(4) for _ in range(4)],
            'color_envelope_ref': self._read_int(4),
            'color_envelope_offset': self._read_int(4),
            'image_ref': self._read_int(4),
            'data_ptr': self._read_int(4),
            'name': self._read_istr(3),
            'data_tele_ptr': self._read_int(4),
            'data_speedup_ptr': self._read_int(4),
            'data_front_ptr': self._read_int(4),
            'data_switch_ptr': self._read_int(4),
            'data_tune_ptr': self._read_int(4)
        }

        if not size == 80:
            raise ValueError()

        if not value['version'] == 3:
            raise ValueError()

        return value

    def _read_item_layer_quad(self, size: int):
        value: dict[str, Union[int, bytes, list[int]]] = {
            'version': self._read_int(4),
            'num_quads': self._read_int(4),
            'data_ptr': self._read_int(4),
            'image_ref': self._read_int(4),
            'name': self._read_istr(3)
        }

        if not size == 28:
            raise ValueError()

        if not value['version'] == 2:
            raise ValueError()

        return value

    def _read_item_layer_sound(self, size: int, deprecated: int):
        value: dict[str, Union[int, bytes, list[int]]] = {
            'version': self._read_int(4),
            'num_sources': self._read_int(4),
            'data_ptr': self._read_int(4),
            'sound_ref': self._read_int(4),
            'name': self._read_istr(3),
            'deprecated': deprecated
        }

        if not size == 28:
            raise ValueError()

        if not value['version'] == 2:  # TODO: this might be wrong
            raise ValueError()

        return value


if __name__ == '__main__':
    df = DataFileReader('HeyTux2.map')
    print(df.get_item(2, 0))
