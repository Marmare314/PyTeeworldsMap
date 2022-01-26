from PIL import Image

from pytwmap.constants import TileFlag
from pytwmap.items import ItemImage, ItemImageExternal, ItemLayer, ItemManager, ItemQuadLayer, ItemTileLayer
from pytwmap.tilemanager import TileManager, VanillaTileManager
from pytwmap.twmap import TWMap

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame  # noqa: E402


map_slice = tuple[int, int, int, int]


class MapRenderer:
    def __init__(self, map_ref: TWMap):
        self._map_ref = map_ref
        self._tilesets: dict[ItemImage, list[pygame.surface.Surface]] = {}

        self._useless_manager = ItemManager()
        self._entities = ItemImageExternal(self._useless_manager, 'ddnet')

    def _add_tileset(self, image: ItemImage):
        assert image.width == 1024 and image.height == 1024

        tiles: list[pygame.surface.Surface] = []
        img = pygame.image.frombuffer(
            image.image.tobytes(),  # type: ignore
            (image.width, image.height),
            'RGBA'
        )

        for y in range(0, image.height, 64):
            for x in range(0, image.width, 64):
                tile = pygame.Surface((64, 64), flags=pygame.SRCALPHA)
                tile.blit(img, (0, 0), (x, y, 64, 64))
                tiles.append(tile)

        self._tilesets[image] = tiles

    def generate_tilesets(self):
        self._tilesets = {}
        for layer in self._map_ref.layers:
            if isinstance(layer, ItemTileLayer):
                if layer.image is not None:
                    self._add_tileset(layer.image)
        self._add_tileset(self._entities)

    def render_layer(self, layer: ItemLayer, slice: map_slice, tile_scale: int) -> Image.Image:
        _, _, w, h = slice
        return Image.frombytes('RGBA', (w * tile_scale, h * tile_scale), pygame.image.tostring(self.render_layer(layer, slice, tile_scale), 'RGBA'))  # type: ignore

    def _render_layer(self, layer: ItemLayer, slice: map_slice, tile_scale: int):
        if isinstance(layer, ItemTileLayer):
            return self._render_tile_layer(layer, slice, tile_scale)  # type: ignore
        elif isinstance(layer, ItemQuadLayer):
            raise NotImplementedError()
        else:
            raise RuntimeError('cannot render layer')

    def _render_tile_layer(self, layer: ItemTileLayer[TileManager], slice: map_slice, tile_scale: int):
        x_0, y_0, w, h = slice

        if layer.is_game or layer.is_front or layer.is_tele or layer.is_switch or layer.is_tune or layer.is_speedup:
            image_item = self._entities
        elif layer.image is None:
            raise RuntimeError('cannot render non-game layer without image')
        else:
            image_item: ItemImage = layer.image
        if image_item not in self._tilesets:
            raise RuntimeError('image reference not found')

        tileset = self._tilesets[image_item]

        buffer = pygame.Surface((w * tile_scale, h * tile_scale), flags=pygame.SRCALPHA)

        for dx in range(w):
            for dy in range(h):
                if x_0 + dx < 0 or y_0 + dy < 0:
                    continue
                t = layer.tiles.get_id(x_0 + dx, y_0 + dy)
                tile_img = tileset[t]
                if isinstance(layer.tiles, VanillaTileManager):
                    if layer.tiles.has_flag(x_0 + dx, y_0 + dy, TileFlag.VFLIP):
                        tile_img = pygame.transform.flip(tile_img, True, False)
                    if layer.tiles.has_flag(x_0 + dx, y_0 + dy, TileFlag.HFLIP):
                        tile_img = pygame.transform.flip(tile_img, False, True)
                    if layer.tiles.has_flag(x_0 + dx, y_0 + dy, TileFlag.ROTATE):
                        tile_img = pygame.transform.rotate(tile_img, -90)
                tile_img = pygame.transform.scale(tile_img, (tile_scale, tile_scale))
                buffer.blit(tile_img, (dx * tile_scale, dy * tile_scale))

        return buffer
