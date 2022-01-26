from enum import IntEnum


class ItemType(IntEnum):
    VERSION = 0
    INFO = 1
    IMAGE = 2
    ENVELOPE = 3
    GROUP = 4
    LAYER = 5
    ENVPOINTS = 6
    SOUND = 7


class LayerType(IntEnum):
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


class LayerFlags(IntEnum):
    DETAIL = 1


class TileLayerFlags(IntEnum):
    GAME = 1
    TELE = 2
    SPEEDUP = 4
    FRONT = 8
    SWITCH = 16
    TUNE = 32


class TileFlag(IntEnum):
    VFLIP = 1
    HFLIP = 2
    OPAQUE = 4
    ROTATE = 8


class CurveType(IntEnum):
    STEP = 0
    LINEAR = 1
    SLOW = 2
    FAST = 3
    SMOOTH = 4
    BEZIER = 5  # envelope version 3 (vanilla)


# TODO: seperate them into GameTileType, TeleTileType, ...
# class EntityTileType(IntEnum):
#     AIR = 0
#     SOLID = 1
#     DEATH = 2
#     NOHOOK = 3
#     NOLASER = 4
#     THROUGH_CUT = 5
#     THROUGH = 6
#     JUMP = 7
#     FREEZE = 9
#     TELEINEVIL = 10
#     UNFREEZE = 11
#     DFREEZE = 12
#     DUNFREEZE = 13
#     TELEINWEAPON = 14
#     TELEINHOOK = 15
#     WALLJUMP = 16
#     EHOOK_ENABLE = 16
#     EHOOK_DISABLE = 17
#     HIT_ENABLE = 18
#     HIT_DISABLE = 19
#     SOLO_ENABLE = 20
#     SOLO_DISABLE = 21

#     # Switches
#     TILE_SWITCHTIMEDOPEN = 22
#     TILE_SWITCHTIMEDCLOSE = 23
#     TILE_SWITCHOPEN = 24
#     TILE_SWITCHCLOSE = 25
#     TILE_TELEIN = 26
#     TILE_TELEOUT = 27
#     TILE_BOOST = 28
#     TILE_TELECHECK = 29
#     TILE_TELECHECKOUT = 30
#     TILE_TELECHECKIN = 31
#     TILE_REFILL_JUMPS = 32
#     TILE_START = 33
#     TILE_FINISH = 34
#     TILE_CHECKPOINT_FIRST = 35
#     TILE_CHECKPOINT_LAST = 59
#     TILE_STOP = 60
#     TILE_STOPS = 61
#     TILE_STOPA = 62
#     TILE_TELECHECKINEVIL = 63
#     TILE_CP = 64
#     TILE_CP_F = 65
#     TILE_THROUGH_ALL = 66
#     TILE_THROUGH_DIR = 67
#     TILE_TUNE = 68
#     TILE_OLDLASER = 71,
#     TILE_NPC = 72
#     TILE_EHOOK = 73
#     TILE_NOHIT = 74
#     TILE_NPH = 75
#     TILE_UNLOCK_TEAM = 76
#     TILE_ADD_TIME = 79
#     TILE_NPC_DISABLE = 88
#     TILE_UNLIMITED_JUMPS_DISABLE = 89
#     TILE_JETPACK_DISABLE = 90
#     TILE_NPH_DISABLE = 91
#     TILE_SUBTRACT_TIME = 95,
#     TILE_TELE_GUN_ENABLE = 96,
#     TILE_TELE_GUN_DISABLE = 97,
#     TILE_ALLOW_TELE_GUN = 98,
#     TILE_ALLOW_BLUE_TELE_GUN = 99,
#     TILE_NPC_ENABLE = 104,
#     TILE_UNLIMITED_JUMPS_ENABLE = 105
#     TILE_JETPACK_ENABLE = 106
#     TILE_NPH_ENABLE = 107
#     TILE_TELE_GRENADE_ENABLE = 112
#     TILE_TELE_GRENADE_DISABLE = 113
#     TILE_TELE_LASER_ENABLE = 128
#     TILE_TELE_LASER_DISABLE = 129
#     TILE_CREDITS_1 = 140
#     TILE_CREDITS_2 = 141
#     TILE_CREDITS_3 = 142
#     TILE_CREDITS_4 = 143
#     TILE_LFREEZE = 144
#     TILE_LUNFREEZE = 145
#     TILE_CREDITS_5 = 156
#     TILE_CREDITS_6 = 157
#     TILE_CREDITS_7 = 158
#     TILE_CREDITS_8 = 159
#     TILE_ENTITIES_OFF_1 = 190
#     TILE_ENTITIES_OFF_2 = 191
