from __future__ import annotations

import zlib
from PIL import Image


def safe_chr(i):
    return chr(max(0, min(i if i >= 0 else 256 + i, 256)))


class DataFile:
    def __init__(self, path: str):
        # open file and store bytes
        with open(path, 'rb') as file:
            self._content = file.read()

        # init reading position
        self._pointer = 0

        # validate file format
        magic = self.read(4)
        if not (magic == b'DATA' or magic == b'ATAD'):
            raise ValueError('magic string not correct')

        version = self.read_int(4)
        if not version == 4:
            raise ValueError('only datafile version 4 supported')

        # read header
        self.size = self.read_int(4)
        self.swaplen = self.read_int(4)
        self.num_item_types = self.read_int(4)
        self.num_items = self.read_int(4)
        self.num_data = self.read_int(4)
        self.item_size = self.read_int(4)
        self.data_size_unc = self.read_int(4)

        # TODO: read itemtypes
        for _ in range(self.num_item_types):
            self.read_int(4)
            self.read_int(4)
            self.read_int(4)

        # read offsets
        self._item_offsets = [self.read_int(4) for _ in range(self.num_items)]
        self._data_offsets = [self.read_int(4) for _ in range(self.num_data)]
        self._data_sizes = [self.read_int(4) for _ in range(self.num_data)]

        # calculate data section start
        self._data_start = self.num_item_types * 12
        self._data_start += (self.num_items + self.num_data) * 4
        self._data_start += self.num_data * 4  # only version 4
        self._data_start += self.item_size
        self._data_start += 36

    def read(self, num_bytes: int):
        value = self._content[self._pointer:self._pointer + num_bytes]
        self._pointer += num_bytes
        return value

    def read_int(self, num_bytes: int, signed: bool = True):
        return int.from_bytes(self.read(num_bytes), byteorder='little', signed=signed)

    def read_istr(self, num_bytes: int):
        return ''.join([''.join([
            safe_chr(((val >> 24) & 0xff)-128),
            safe_chr(((val >> 16) & 0xff)-128),
            safe_chr(((val >> 8) & 0xff)-128),
            safe_chr((val & 0xff)-128),
        ]) for val in self.read(num_bytes)]).partition('\x00')[0][::-1]

    def get_data(self, data_ptr: int):
        offset = self._data_offsets[data_ptr]
        next_offset = self._data_offsets[data_ptr + 1] if data_ptr + 1 < len(self._data_offsets) else self.size
        return zlib.decompress(self._content[self._data_start + offset:self._data_start + next_offset])

    def get_data_str(self, data_ptr: int):
        return self.get_data(data_ptr)[:-1].decode('ascii')


class ItemVersion:
    def __init__(self):
        pass

    @staticmethod
    def from_data(data: DataFile, size: int):
        if not size == 4:
            raise ValueError('ItemVersion: size should be 4')

        version = data.read_int(4)
        if not version == 1:
            raise ValueError('ItemVersion: expected version 1')

        return ItemVersion()


class ItemInfo:
    def __init__(self, author: str, mapversion: str, credits: str, license: str, settings: list[str]):
        self.author = author
        self.mapversion = mapversion
        self.credits = credits
        self.license = license
        self.settings = settings

    @staticmethod
    def from_data(data: DataFile, size: int):
        if not size == 24:
            raise ValueError('ItemInfo: size should be 24')

        version = data.read_int(4)
        if not version == 1:
            raise ValueError('ItemInfo: expected version 1')

        for _ in range(5):
            if not data.read_int(4) == -1:
                raise ValueError('not implemented')

        return ItemInfo('', '', '', '', [''])


class ItemImage:
    def __init__(self, image: Image.Image, external: int, name: str):
        self.image = image
        self.external = external
        self.name = name

    @staticmethod
    def from_data(data: DataFile, size: int):
        if not size == 24:
            raise ValueError('ItemImage: size should be 24')

        version = data.read_int(4)
        if not version == 1:
            raise ValueError('ItemImage: expected version 1')

        # TODO: check if ptr are >0
        width = data.read_int(4)
        height = data.read_int(4)
        external = data.read_int(4)
        name_ptr = data.read_int(4)
        data_ptr = data.read_int(4)

        if external:
            name = data.get_data_str(name_ptr)
            img = Image.open(f'mapres/{name}.png')
            ItemImage(img, external, name)
        else:
            img_data = data.get_data(data_ptr)
            name = data.get_data_str(name_ptr)
            img = Image.frombytes('RGBA', (width, height), img_data)  # type: ignore
            return ItemImage(img, external, name)


class ItemEnvelope:
    def __init__(self):
        pass

    @staticmethod
    def from_data(data: DataFile, size: int):
        if not size == 52:
            raise ValueError('ItemEnvelope: size should be 52')

        version = data.read_int(4)
        if not version == 2:
            raise ValueError('ItemEnvelope: expected version 2')

        channels = data.read_int(4)
        start_point = data.read_int(4)
        num_points = data.read_int(4)
        name = data.read_istr(32)
        synch = data.read_int(4)


class ItemGroup:
    def __init__(self):
        pass

    @staticmethod
    def from_data(data: DataFile, size: int):
        if not size == 60:
            raise ValueError('ItemGroup: expected size 60')

        data.read(60)


class ItemLayer:
    def __init__(self, flags: int):
        pass

    @staticmethod
    def from_data(data: DataFile, size: int):
        data.read_int(4)  # version is not used
        layer_type = data.read_int(4)
        flags = data.read_int(4)

        if layer_type == 2:
            return Tilelayer._from_data(data, size - 12, flags)
        elif layer_type == 3:
            return QuadLayer._from_data(data, size - 12, flags)
        else:
            raise ValueError('ItemLayer: layer_type not implemented')


class TWColor:
    def __init__(self):
        pass

    @staticmethod
    def from_data(data: DataFile):
        # TODO
        data.read_int(4)
        data.read_int(4)
        data.read_int(4)
        data.read_int(4)
        return TWColor()


class Tilelayer(ItemLayer):
    @staticmethod
    def _from_data(data: DataFile, size: int, flags: int):
        if not size == 80:
            raise ValueError('TileLayer: expected size 76')

        version = data.read_int(4)
        if not version == 3:
            raise ValueError('TileLayer: expected version 3')

        width = data.read_int(4)
        height = data.read_int(4)
        flags = data.read_int(4)
        color = TWColor.from_data(data)
        color_envelope_ref = data.read_int(4)
        color_envelope_offset = data.read_int(4)
        image_ref = data.read_int(4)
        data_ptr = data.read_int(4)
        name = data.read_istr(12)
        data_tele_ptr = data.read_int(4)
        data_speedup_ptr = data.read_int(4)
        data_front_ptr = data.read_int(4)
        data_switch_ptr = data.read_int(4)
        data_tune_ptr = data.read_int(4)


class QuadLayer(ItemLayer):
    @staticmethod
    def _from_data(data: DataFile, size: int, flags: int):
        if not size == 28:
            raise ValueError('QuadLayer: expected size 28')

        version = data.read_int(4)
        if not version == 2:
            raise ValueError('QuadLayer: expected version 2')

        num_quads = data.read_int(4)
        quad_ptr = data.read_int(4)
        image_ref = data.read_int(4)
        name = data.read_istr(12)


class ItemEnvPoints:
    @staticmethod
    def from_data(data: DataFile, size: int):
        # if not size == 24:
        #     raise ValueError('ItemEnvPoints: expected size 24')

        data.read(size)


class ItemUUID:
    @staticmethod
    def from_data(data: DataFile, size: int):
        pass


class TWMap:
    def __init__(self):
        pass

    @staticmethod
    def open(path: str):
        data = DataFile(path)

        # read items
        for _ in range(data.num_items):
            type_and_id = data.read_int(4)
            item_type = (type_and_id >> 16) & 0xffff
            size = data.read_int(4)
            if item_type == 0:
                ItemVersion.from_data(data, size)
            elif item_type == 1:
                ItemInfo.from_data(data, size)
            elif item_type == 2:
                ItemImage.from_data(data, size)
            elif item_type == 3:
                ItemEnvelope.from_data(data, size)
            elif item_type == 4:
                ItemGroup.from_data(data, size)
            elif item_type == 5:
                ItemLayer.from_data(data, size)
            elif item_type == 6:
                ItemEnvPoints.from_data(data, size)
            elif item_type == 0xffff:
                ItemUUID.from_data(data, size)
            else:
                raise ValueError('TWMap: item_type not recognized')


if __name__ == '__main__':
    m = TWMap()
    m.open('HeyTux2.map')
