from PIL import Image
from typing import Tuple

from pytwmap.constants import TileFlag
from pytwmap.items import ItemImage, ItemImageExternal, ItemLayer, ItemQuadLayer, ItemTileLayer
from pytwmap.tilemanager import TileManager, VanillaTileManager
from pytwmap.twmap import TWMap

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame  # noqa: E402


class MapRenderer:
    def __init__(self, image_size: Tuple[int, int], map_ref: TWMap):
        self._map_ref = map_ref
        self._tilesets: dict[ItemImage, list[pygame.surface.Surface]] = {}

        self._width, self._height = image_size
        self._image_buffer = pygame.surface.Surface = pygame.Surface(image_size, flags=pygame.SRCALPHA)

        self._entities = ItemImageExternal('ddnet')

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

    def clear_buffer(self):
        self._image_buffer = pygame.Surface((self._width, self._height), flags=pygame.SRCALPHA)

    def get_image(self) -> Image.Image:
        return Image.frombytes('RGBA', (self._width, self._height), pygame.image.tostring(self._image_buffer, 'RGBA'))  # type: ignore

    def render_layer(self, layer: ItemLayer, x0: int, y0: int, tile_scale: int):
        if isinstance(layer, ItemTileLayer):
            return self._render_tile_layer(layer, x0, y0, tile_scale)  # type: ignore
        elif isinstance(layer, ItemQuadLayer):
            raise NotImplementedError()
        else:
            raise RuntimeError('cannot render layer')

    def _render_tile_layer(self, layer: ItemTileLayer[TileManager], x0: int, y0: int, tile_scale: int):
        if layer in [self._map_ref.game_layer, self._map_ref.tele_layer, self._map_ref.speedup_layer, self._map_ref.front_layer, self._map_ref.switch_layer, self._map_ref.tune_layer]:
            image_item = self._entities
        elif layer.image is None:
            raise RuntimeError('cannot render non-game layer without image')
        else:
            image_item: ItemImage = layer.image
        if image_item not in self._tilesets:
            raise RuntimeError('image reference not found')

        tileset = self._tilesets[image_item]

        # buffer = pygame.Surface((w * tile_scale, h * tile_scale), flags=pygame.SRCALPHA)

        for dx in range(self._width // tile_scale):
            for dy in range(self._height // tile_scale):
                if x0 + dx < 0 or layer.width <= x0 + dx or y0 + dy < 0 or layer.height <= y0 + dy:
                    continue

                t = layer.tiles.get_id(x0 + dx, y0 + dy)
                tile_img = tileset[t]
                if isinstance(layer.tiles, VanillaTileManager):
                    if layer.tiles.has_flag(x0 + dx, y0 + dy, TileFlag.VFLIP):
                        tile_img = pygame.transform.flip(tile_img, True, False)
                    if layer.tiles.has_flag(x0 + dx, y0 + dy, TileFlag.HFLIP):
                        tile_img = pygame.transform.flip(tile_img, False, True)
                    if layer.tiles.has_flag(x0 + dx, y0 + dy, TileFlag.ROTATE):
                        tile_img = pygame.transform.rotate(tile_img, -90)
                tile_img = pygame.transform.scale(tile_img, (tile_scale, tile_scale))
                self._image_buffer.blit(tile_img, (dx * tile_scale, dy * tile_scale))
