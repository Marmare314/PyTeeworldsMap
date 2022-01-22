from enum import IntEnum


class EnumItemType(IntEnum):
    VERSION = 0
    INFO = 1
    IMAGE = 2
    ENVELOPE = 3
    GROUP = 4
    LAYER = 5
    ENVPOINTS = 6
    SOUND = 7


class EnumLayerType(IntEnum):
    INVALID = 0
    GAME = 1
    TILES = 2
    QUADS = 3
    FRONT = 4
    TELE = 5
    SPEEDUP = 6
    SWITCH = 7
    TUNE = 8
    SOUNDS_DEPCRECATED = 9
    SOUNDS = 10


class EnumTileLayerFlags(IntEnum):
    GAME = 1
    TELE = 2
    SPEEDUP = 4
    FRONT = 8
    SWITCH = 16
    TUNE = 32


class EnumCurveType(IntEnum):
    STEP = 0
    LINEAR = 1
    SLOW = 2
    FAST = 3
    SMOOTH = 4
    BEZIER = 5  # envelope version 3 (vanilla)
