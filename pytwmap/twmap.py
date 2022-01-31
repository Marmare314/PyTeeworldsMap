from typing import Optional
from pytwmap.datafile_reader import DataFileReader
from pytwmap.datafile_writer import DataFileWriter
from pytwmap.items import ItemQuadLayer, ItemVersion, ItemInfo, ItemTileLayer, ItemGroup
from pytwmap.tilemanager import SpeedupTileManager, SwitchTileManager, TeleTileManager, TuneTileManager, VanillaTileManager


# TODO: make exceptions/asserts consistent
# TODO: try to remove type ignores


class TWMap:
    def __init__(self):
        self.version = ItemVersion(version=1)
        self.info = ItemInfo()
        self.game_layer = ItemTileLayer(
            tiles=VanillaTileManager(50, 50),
            name='Game'
        )
        self.groups = [ItemGroup(
            layers=[self.game_layer],
            name='Game'
        )]

    def open(self, path: str):
        with open(path, 'rb') as file:
            data = DataFileReader(file.read())

        self.version = data.get_version()
        self.info = data.get_info()

        self.groups = data.get_groups()

        if data.game_layer is None:
            raise RuntimeError('no gamelayer found')
        self.game_layer = data.game_layer
        self.tele_layer = data.tele_layer
        self.speedup_layer = data.speedup_layer
        self.front_layer = data.front_layer
        self.switch_layer = data.switch_layer
        self.tune_layer = data.tune_layer

    def save(self, path: str):
        data = DataFileWriter()

        data.set_special_layers(
            self.game_layer,
            self.tele_layer,
            self.speedup_layer,
            self.front_layer,
            self.switch_layer,
            self.tune_layer
        )

        data.register_version(self.version)
        data.register_info(self.info)

        for group in self.groups:
            data.register_group(group)

        return data.write(path)

    def _images_generator(self):
        for layer in self.layers:
            if isinstance(layer, ItemTileLayer) or isinstance(layer, ItemQuadLayer):
                if layer.image is not None:
                    yield layer.image

    @property
    def images(self):
        return list(self._images_generator())

    def _layers_generator(self):
        for group in self.groups:
            for layer in group.layers:
                yield layer

    @property
    def layers(self):
        return list(self._layers_generator())

    @property
    def design_layers(self):
        for layer in self._layers_generator():
            if layer not in self.gameplay_layers:
                yield layer

    def _gameplay_layers_generator(self):
        for layer in self._layers_generator():
            if layer == self.game_layer or layer == self.tele_layer or layer == self.speedup_layer or layer == self.front_layer or layer == self.switch_layer or layer == self.tune_layer:
                if layer is not None:
                    yield layer

    @property
    def gameplay_layers(self):
        return list(self._gameplay_layers_generator())

    @property
    def game_layer(self):
        if self._game_layer is None:
            raise RuntimeError('no gamelayer found')
        return self._game_layer

    @game_layer.setter
    def game_layer(self, layer: ItemTileLayer[VanillaTileManager]):
        self._game_layer = layer

    # TODO: should these be exposed or properties?
    @property
    def tele_layer(self):
        return self._tele_layer

    @tele_layer.setter
    def tele_layer(self, layer: Optional[ItemTileLayer[TeleTileManager]]):
        self._tele_layer = layer

    @property
    def speedup_layer(self):
        return self._speedup_layer

    @speedup_layer.setter
    def speedup_layer(self, layer: Optional[ItemTileLayer[SpeedupTileManager]]):
        self._speedup_layer = layer

    @property
    def front_layer(self):
        return self._front_layer

    @front_layer.setter
    def front_layer(self, layer: Optional[ItemTileLayer[VanillaTileManager]]):
        self._front_layer = layer

    @property
    def switch_layer(self):
        return self._switch_layer

    @switch_layer.setter
    def switch_layer(self, layer: Optional[ItemTileLayer[SwitchTileManager]]):
        self._switch_layer = layer

    @property
    def tune_layer(self):
        return self._tune_layer

    @tune_layer.setter
    def tune_layer(self, layer: Optional[ItemTileLayer[TuneTileManager]]):
        self._tune_layer = layer
