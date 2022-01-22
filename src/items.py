from PIL import Image
from constants import EnumItemType


# TODO: make sure references are internal and valid
class ItemManager:
    def __init__(self):
        self.version = ItemVersion(3)
        self.info = ItemInfo()
        self.images: dict[int, ItemImage] = {}
        # envelopes
        self.groups: dict[int, ItemGroup] = {}

    def insert(self, item: 'Item'):
        pass

    def insert_with_id(self, item: 'Item', id: int):
        if isinstance(item, ItemVersion):
            self.version = item
        elif isinstance(item, ItemInfo):
            self.info = item
        else:
            raise ValueError('type of item not known')

    def clear(self):
        pass


class Item:
    type_id: int  # TODO: is this needed?


class ItemVersion(Item):
    type_id = EnumItemType.VERSION

    def __init__(self, version: int):
        self.version = version


class ItemInfo(Item):
    type_id = EnumItemType.INFO

    def __init__(self, author: str = '', mapversion: str = '', credits: str = '', license: str = '', settings: list[str] = []):
        self.author = author
        self.mapversion = mapversion
        self.credits = credits
        self.license = license
        self.settings = settings


class ItemImage(Item):
    type_id = EnumItemType.IMAGE

    def __init__(self):
        self._image = None
        self._name = None
        self._external = None

    def set_internal(self, image: Image.Image, name: str):
        self._image = image
        self._name = name
        self._external = False

    def set_external(self, name: str):
        # TODO: assert name is in externals
        self._image = Image.open(f'mapres/{name}.png')
        self._name = name
        self._external = True

    @property
    def image(self):
        return self._image

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        if self._external:
            raise ValueError('Cannot change name of external image')
        self._name = name


class ItemEnvelope(Item):
    type_id = EnumItemType.ENVELOPE


class ItemLayer(Item):
    type_id = EnumItemType.LAYER

    def __init__(self, detail: bool):
        self.detail = detail


class TileLayer(ItemLayer):
    pass


class QuadLayer(ItemLayer):
    pass


class SoundLayer(ItemLayer):
    pass


class ItemGroup(Item):
    type_id = EnumItemType.GROUP


class ItemSound(Item):
    type_id = EnumItemType.SOUND
