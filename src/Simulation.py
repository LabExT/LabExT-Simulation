#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Type

import src.CLI as cli

from src.Models import StageModel, ChipModel, WorldModel
from src.Plotter import Plotter

from LabExT.Wafer.Chip import Chip
from LabExT.Movement.MoverNew import MoverNew, Orientation, State

from vedo import settings, Axes

settings.allowInteraction = True

class Simulation:

    CHIP_VIEW = 1
    STAGE_VIEW = 0

    def __init__(self, mover, chip):
        self.mover: Type[MoverNew] = mover
        self.chip: Type[Chip] = chip

        self.stage_plotters = {}

        self.__setup_calibrations__()
        self.__setup_chip__()


    def __setup_calibrations__(self):
        if not self.mover.has_connected_stages:
            cli.error("Mover has no connected stages. Cannot simulate stages!")
            return

        for calibration in self.mover.calibrations.values():
            stage_plotter = Plotter(withDoubleView=False)

            # world_model = WorldModel(3e4, 3e4, 3e4)
            stage_model = StageModel.build_from_calibration(calibration)

            calibration.stage.__register__simulation__([stage_plotter], stage_model)

            stage_plotter.show(stage_model.mesh, interactive=False)
            # stage_plotter.at(self.CHIP_VIEW).show(world_model.mesh, stage_model.mesh, interactive=False)

            self.stage_plotters[calibration] = stage_plotter

    def __setup_chip__(self):
        if not self.chip:
            cli.error("Chip is not defined for simulation!")
            return

        for calibration, stage_plotter in self.stage_plotters.items():
            transformation = None
            if calibration.state == State.FULLY_CALIBRATED:
                transformation = calibration.full_transformation
            elif calibration.state == State.SINGLE_POINT_FIXED:
                transformation = calibration.single_point_transformation

            chip_model = ChipModel.from_chip(self.chip, transformation)
            stage_plotter.show(chip_model.mesh, interactive=False)


    def move_to_device(self, device):
        self.mover.move_to_device(device)
