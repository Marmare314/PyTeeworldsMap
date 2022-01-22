from enum import IntEnum


class ItemType(IntEnum):
    VERSION = 0
    INFO = 1
    IMAGE = 2
    ENVELOPE = 3
    GROUP = 4
    LAYER = 5
    ENVPOINT = 6
    UUID = 0xffff
