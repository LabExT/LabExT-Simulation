#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import combinations
from typing import Type
from enum import Enum, auto

from LabExT.Wafer.Chip import Chip
from LabExT.Movement.MoverNew import MoverNew, Stage

import labext_simulation.cli as cli
from labext_simulation.models import ChipModel, StageModel

from vedo import Plotter, settings

settings.allowInteraction = True



class SimulationPlotter(Plotter):
    def __init__(self):
        super().__init__(
            title="LabExT Simulation",
            size=(1080, 1440),
            axes=dict(
                xtitle='X [um]',
                ytitle='Y [um]',
                ztitle='Z [um]',
                numberOfDivisions=20,
                axesLineWidth= 2,
                gridLineWidth= 1,
                zxGrid2=True,
                yzGrid2=True, 
                xyPlaneColor='green7',
                xyGridColor='dg', 
                xyAlpha=0.1,
                xTitlePosition=0.5,
                xTitleJustify="top-center",
                yTitlePosition=0.5,
                yTitleJustify="top-center",
                zTitlePosition=0.5,
                zTitleJustify="top-center"))

class Simulation:

    def __init__(self, mover, chip) -> None:
        self.mover: Type[MoverNew] = mover
        self.chip: Type[Chip] = chip

        self.chip_model = ChipModel.build(self.chip)

        self.stage_models = {}
        self.stage_collision_meshes = {}
        for identifier, calibration in enumerate(self.mover.calibrations.values()):
            stage_model = StageModel.build(calibration)
            calibration.stage.set_simulation(self, identifier, stage_model.model_position)
            self.stage_models[identifier] = stage_model

        self.plotter = SimulationPlotter()
        self.plotter.show(self.get_all_meshes(), interactive=False)

    @property
    def is_realtime(self):
        return False

    def get_all_meshes(self):
        meshes = [model.mesh for model in self.stage_models.values()]
        if self.chip_model:
            meshes.append(self.chip_model.mesh)

        return meshes 

    def render_stage_model(self, model_identifier: str, pos: list):
        model = self.stage_models[model_identifier]
        model.pos(*pos)
        self._detect_collision()
        self.plotter.render()


    def _detect_collision(self):
        for model_a, model_b in combinations(self.stage_models.values(), 2):
            collision_mesh = model_a.collide(model_b)
            if collision_mesh.points().size > 0:
                cli.error("Collision detected.")

            

    def simulate(self, ):
        pass


    def move_to_all_devices(self):
        for device in self.chip._devices.values():
            self.mover.move_to_device(device)