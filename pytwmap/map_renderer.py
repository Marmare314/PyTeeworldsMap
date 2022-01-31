from PIL import Image

from pytwmap.constants import TileFlag
from pytwmap.items import ItemImage, ItemImageExternal, ItemLayer, ItemQuadLayer, ItemTileLayer
from pytwmap.tilemanager import TileManager, VanillaTileManager
from pytwmap.twmap import TWMap

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame  # noqa: E402


class MapRenderer:
    def __init__(self, map_ref: TWMap, image_size: tuple[int, int], viewer_pos: tuple[int, int] = (0, 0), time: int = 0):
        self._map_ref = map_ref
        self._tilesets: dict[ItemImage, list[pygame.surface.Surface]] = {}
        self._viewer_pos_x, self._viewer_pos_y = viewer_pos
        self._time = 0

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

    def render_map_design(self, x_start: int, y_start: int, tile_scale: int):
        for layer in self._map_ref.design_layers:
            self.render_layer(layer, x_start, y_start, tile_scale)

    def render_map_gameplay(self, x_start: int, y_start: int, tile_scale: int):
        for layer in self._map_ref.gameplay_layers:
            self.render_layer(layer, x_start, y_start, tile_scale)

    def render_layer(self, layer: ItemLayer, x_start: int, y_start: int, tile_scale: int):
        if isinstance(layer, ItemTileLayer):
            self._render_tile_layer(layer, x_start, y_start, tile_scale)  # type: ignore
        elif isinstance(layer, ItemQuadLayer):
            raise NotImplementedError()
        else:
            raise RuntimeError('cannot render layer')

    def _render_tile_layer(self, layer: ItemTileLayer[TileManager], x_start: int, y_start: int, tile_scale: int):
        if layer in [self._map_ref.game_layer, self._map_ref.tele_layer, self._map_ref.speedup_layer, self._map_ref.front_layer, self._map_ref.switch_layer, self._map_ref.tune_layer]:
            image_item = self._entities
        elif layer.image is None:
            raise RuntimeError('cannot render non-game layer without image')
        else:
            image_item: ItemImage = layer.image
        if image_item not in self._tilesets:
            raise RuntimeError('image reference not found')

        offset_x = 0
        offset_y = 0
        parallax_x = 100
        parallax_y = 100

        for group in self._map_ref.groups:
            if layer in group.layers:
                offset_x = group.x_offset
                offset_y = group.y_offset
                parallax_x = group.x_parallax
                parallax_y = group.y_parallax

        tile_x, tile_y = x_start // 32, y_start // 32
        offset_x += ((x_start % 32) * tile_scale) // 32
        offset_y += ((y_start % 32) * tile_scale) // 32

        offset_x += (parallax_x * self._viewer_pos_x) // 100
        offset_y += (parallax_y * self._viewer_pos_y) // 100

        tileset = self._tilesets[image_item]
        for dx in range(self._width // tile_scale + 1):
            for dy in range(self._height // tile_scale + 1):
                if tile_x + dx < 0 or layer.width <= tile_x + dx or tile_y + dy < 0 or layer.height <= tile_y + dy:
                    continue

                t = layer.tiles.get_id(tile_x + dx, tile_y + dy)

                # blend color
                # TODO: envelope color
                tile_img = pygame.Surface((64, 64), flags=pygame.SRCALPHA)
                tile_img.fill(layer.color)
                tile_img.blit(tileset[t], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                # transform tiles
                if isinstance(layer.tiles, VanillaTileManager):
                    if layer.tiles.has_flag(tile_x + dx, tile_y + dy, TileFlag.VFLIP):
                        tile_img = pygame.transform.flip(tile_img, True, False)
                    if layer.tiles.has_flag(tile_x + dx, tile_y + dy, TileFlag.HFLIP):
                        tile_img = pygame.transform.flip(tile_img, False, True)
                    if layer.tiles.has_flag(tile_x + dx, tile_y + dy, TileFlag.ROTATE):
                        tile_img = pygame.transform.rotate(tile_img, -90)

                # scale tile
                tile_img = pygame.transform.scale(tile_img, (tile_scale, tile_scale))
                self._image_buffer.blit(tile_img, (dx * tile_scale - offset_x, dy * tile_scale - offset_y))
