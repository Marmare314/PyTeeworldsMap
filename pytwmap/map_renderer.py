from PIL import Image

from pytwmap.constants import TileFlag
from pytwmap.items import ItemImage, ItemImageExternal, ItemLayer, ItemQuadLayer, ItemTileLayer
from pytwmap.tilemanager import TileManager, VanillaTileManager
from pytwmap.twmap import TWMap

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame  # noqa: E402


# TODO: use pyopengl


# TRegion = tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]


# def find_coeffs(pa: TRegion, pb: TRegion):
#     matrix: list[list[int]] = []
#     for p1, p2 in zip(pa, pb):
#         matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
#         matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])

#     A = numpy.matrix(matrix, dtype=numpy.float)  # type: ignore
#     B = numpy.array(pb).reshape(8)  # type: ignore

#     res = numpy.dot(numpy.linalg.inv(A.T * A) * A.T, B)  # type: ignore
#     return numpy.array(res).reshape(8)  # type: ignore


class MapRenderer:
    def __init__(self,
                 map_ref: TWMap,
                 image_size: tuple[int, int],
                 viewer_pos: tuple[int, int] = (0, 0),
                 time: int = 0,
                 render_pos: tuple[int, int] = (0, 0),
                 tile_scale: int = 10):
        self._map_ref = map_ref
        self._viewer_pos_x, self._viewer_pos_y = viewer_pos
        self._time = time
        self._render_pos_x, self._render_pos_y = render_pos
        self._tile_scale = tile_scale

        self._width, self._height = image_size
        self._image_buffer: pygame.Surface = pygame.Surface(image_size, flags=pygame.SRCALPHA)
        self._tilesets: dict[ItemImage, list[pygame.Surface]] = {}

        self._entities = ItemImageExternal('ddnet')

        # self._generate_mask()

    # def _generate_mask(self):
    #     self._mask = Image.new('RGBA', (1024, 1024), (0, 0, 0, 255))
    #     for x in range(self._mask.width):
    #         for y in range(self._mask.height):
    #             alph_x = x / 1024
    #             alph_y = y / 1024
    #             self._mask.putpixel((x, y), (0, 0, 0, round(alph_x * alph_y * 255)))

    def _add_tileset(self, image: ItemImage):
        assert image.width == 1024 and image.height == 1024

        tiles: list[pygame.Surface] = []
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

    def render_map_design(self):
        for layer in self._map_ref.design_layers:
            self.render_layer(layer)

    def render_map_gameplay(self):
        for layer in self._map_ref.gameplay_layers:
            self.render_layer(layer)

    def render_layer(self, layer: ItemLayer):
        if isinstance(layer, ItemTileLayer):
            self._render_tile_layer(layer)  # type: ignore
        elif isinstance(layer, ItemQuadLayer):
            self._render_quad_layer(layer)
        else:
            raise RuntimeError('cannot render layer')

    def _quadcoord_to_imgcoord(self, pos: tuple[int, int]):
        x, y = pos
        return (x // 512, y // 512)

    def _render_quad_layer(self, layer: ItemQuadLayer):
        pass
        # if layer.image is None:
        #     for quad in layer.quads:
        #     quad_img = self._mask
        # else:
        #     quad_img = layer.image.image

        # for quad in layer.quads:
        #     coeffs = find_coeffs(
        #         quad.texture_coords,
        #         tuple([self._quadcoord_to_imgcoord(x) for x in quad.corners])
        #     )
        #     quad_img = quad_img.transform((self._width, self._height), Image.PERSPECTIVE, coeffs)  # type: ignore
        #     quad_img_surface = pygame.image.frombuffer(
        #         quad_img.tobytes(),  # type: ignore
        #         (quad_img.width, quad_img.height),
        #         'RGBA'
        #     )
        #     self._image_buffer.blit(quad_img_surface, (0, 0))

    def _render_tile_layer(self, layer: ItemTileLayer[TileManager]):
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

        tile_x, tile_y = self._render_pos_x // 32, self._render_pos_y // 32
        offset_x += ((self._render_pos_x % 32) * self._tile_scale) // 32
        offset_y += ((self._render_pos_y % 32) * self._tile_scale) // 32

        offset_x += (parallax_x * self._viewer_pos_x) // 100
        offset_y += (parallax_y * self._viewer_pos_y) // 100

        tileset = self._tilesets[image_item]
        for dx in range(self._width // self._tile_scale + 1):
            for dy in range(self._height // self._tile_scale + 1):
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
                tile_img = pygame.transform.scale(tile_img, (self._tile_scale, self._tile_scale))
                self._image_buffer.blit(tile_img, (dx * self._tile_scale - offset_x, dy * self._tile_scale - offset_y))
