#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import namedtuple
from contextlib import contextmanager
from itertools import combinations
from tkinter.tix import Tree
from typing import Dict, Type
from tqdm import tqdm

from LabExT.Wafer.Chip import Chip
from LabExT.Movement.MoverNew import MoverNew
from LabExT.Movement.Calibration import Calibration, Axis, Orientation

import labext_simulation.cli as cli
from labext_simulation.models import ChipModel, StageModel

from vedo import Plotter, settings, Text2D
import numpy as np

settings.allowInteraction = True

class SimulationError(RuntimeError):
    pass

class SimulationPlotter(Plotter):
    def __init__(self, offscreen=False):
        super().__init__(
            title="LabExT Simulation",
            offscreen=offscreen,
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
    """
    Base class of all simulations.
    """

    Parameters = namedtuple('Parameters', ['realtime', 'fiber_safety_distance', 'chip_safety_distance', 'sampling_rate'])

    @classmethod
    def build(cls, mover):


        cli.out(f"{cli.GLOBE} Create new Simulation Environment", bold=True, underline=True, color='blue')
        cli.out("The following steps attempt to describe the laboratory environment.\n")

        cli.out(f"{cli.ROBOT} Describe all the stages in the lab:", underline=True, bold=True)
        stage_models={m.orientation: m for m in StageModel.build_list()}

        cli.success("Successfully Environment creation completed. \n")
        return cls(mover, stage_models)

    def __init__(self, mover, stage_models: dict = {}) -> None:
        self.mover: Type[MoverNew] = mover
        self._chip: Type[Chip] = None

        self.parameters: Simulation.Parameters = None

        self.stage_models: Dict[Orientation, Type[StageModel]] = stage_models
        self.chip_model = None

        self.plotter = None
        self.stage_collision_text = None
        self.chip_collision_text = None

        self.chip_collision = False
        self.stage_collision = False

    @property
    def chip(self):
        return self._chip


    @chip.setter
    def chip(self, chip: Type[Chip]):
        self._chip = chip
        self.chip_model = ChipModel.build(chip)
    
    #
    #   Rendering methods
    #

    @contextmanager
    def start_simulation(self):
        # Set new plotter
        self.plotter = SimulationPlotter()
        
        self._set_simulation_parameters()
        self._set_stage_model_meshes()
        self._set_chip_mesh()
        self._set_simulation_info()

        self.plotter.show(interactive=False)

        yield

        self.plotter.interactive().close()


    def render_simulation_step(self):
        self._detect_stage_collision()
        self._detect_chip_collision()
        self.plotter.render()

    #
    #   Simulations cases
    #

    def show_environment(self):
        cli.out("\n\U0001F680 Show current environment", bold=True)

        # Simulate
        with self.start_simulation():
            pass


    def wiggle_axes(self):
        cli.out("\n\U0001F680 Simulating axis wiggeling", bold=True)

        calibration: Type[Calibration] = cli.choice("Select a stage", self.mover.calibrations.values())
        axis = Axis(cli.choice("Select a axis", list(Axis)))
    
        with self.start_simulation():
            calibration.wiggle_axis(axis)

    def wiggle_all_axes(self, calibration: Type[Calibration]):
        cli.out("\n\U0001F680 Simulating wiggeling all axes", bold=True)

        # REMOVE ME
        self.mover.speed_xy = self.mover.DEFAULT_SPEED_XY
        self.mover.speed_z =self.mover.DEFAULT_SPEED_Z
        self.mover.acceleration_xy = 50.0
        self.mover.z_lift = self.mover.DEFAULT_Z_LIFT

        with self.start_simulation():
            for axis in Axis:
                calibration.wiggle_axis(axis)


    def move_to_device(self, device_id=None):
        cli.out("\n\U0001F680 Simulating moving to device", bold=True)

        if not self.chip:
            cli.error("No chip imported!")
            return

        device_id = device_id if device_id else cli.input("Device ID", type=int)
        device = self.chip._devices.get(device_id)
        if device:
            with self.start_simulation():
                self.mover.move_to_device(self.chip, device_id)
        else:
            cli.error("Device not found!")
            self.move_to_device()

        
    def move_to_all_devices(self):
        cli.out("\n\U0001F680 Simulating moving to all devices", bold=True)

        if not self.chip:
            cli.error("No chip imported!")
            return

        with self.start_simulation():
            for device in self.chip._devices.values():
                cli.out(f"Move to device ID: {device._id}", bold=True)
                self.mover.move_to_device(self.chip, device._id)

    def stress_test(self):
        cli.out("\n\U0001F680 Simulating all device combinations", bold=True)

        self.plotter = SimulationPlotter(offscreen=False)
        self.parameters = Simulation.Parameters(
            realtime=False,
            fiber_safety_distance=75,
            chip_safety_distance=10,
            sampling_rate=int(1e4))

        stage_collisions = 0
        chip_collisions = 0

        all_devices = list(self.chip._devices.values())
        for d1, d2 in tqdm(list(combinations(all_devices, 2))):
            # cli.out(f"From Device {d1._id} to Device {d2._id}")
            self._set_stage_model_meshes({
                Orientation.LEFT: d1.input_coordinate.to_numpy(),
                Orientation.RIGHT: d1.output_coordinate.to_numpy(),
            })
            self._set_chip_mesh()
            self._set_simulation_info()
            self.plotter.show(interactive=False)

            self.mover.move_to_device(self.chip, d2._id)

            # cli.out(f"Stage Collision: {self.stage_collision}, Chip Collision: {self.chip_collision}", bold=True)

            if self.stage_collision:
                stage_collisions += 1

            if self.chip_collision:
                chip_collisions += 1

            self.stage_collision = self.chip_collision = False
            self.plotter.clear()

        cli.out(f"Stage Collisions: {stage_collisions}, Chip Collisions: {chip_collisions}")

        self.plotter.interactive().close()
            

    #
    #   Helpers
    #

    def _set_simulation_parameters(self):
        if self.parameters and not cli.confirm("Simulations Parameters already set. Do you want set new ones?", default=False):
            return

        self.parameters = Simulation.Parameters(
            realtime=cli.confirm("Real-time simulation?", default=False),
            fiber_safety_distance=cli.input("Fiber safety distance", default=125.0, type=float),
            chip_safety_distance=cli.input("Chip safety distance", default=10.0, type=float),
            sampling_rate=cli.input("Sampling Rate (higher is faster)", int, int(1e4)))

    def _set_stage_model_meshes(self, model_positions = {}):
        for orientation, model in self.stage_models.items():
            calibration = self.mover._get_calibration(orientation=orientation)
            if calibration:
                model_position = model_positions.get(orientation)
                if model_position is None:
                    stage_position = self._find_model_position(calibration)
                else:
                    stage_position = model.absolute_view.world_to_model(model_position)


                model.set_simulation_parameters(self.parameters.fiber_safety_distance, model_position=stage_position)
                calibration.stage._position = np.array(stage_position)
                
                self.plotter.add(model.mesh())
            else:
                cli.out("Warning: Created model for {}, but no stage assigned to it.".format(orientation))
    def _set_chip_mesh(self):
        if not self.chip_model:
            return

        self.chip_model.set_simulation_parameters(self.parameters.chip_safety_distance)
        self.plotter.add(self.chip_model.mesh())

    def _set_simulation_info(self):
        self.stage_collision_text = Text2D(txt="No stage collision detected", pos="top-left", c="green", alpha=1, s=2)
        self.chip_collision_text = Text2D(txt="No chip collision detected", pos="top-right", c="green", alpha=1, s=2)
        self.plotter.add(self.stage_collision_text, self.chip_collision_text)

    def _find_model_position(self, calibration: Type[Calibration]) -> np.ndarray:
        suggested_position = calibration.stage.get_position() or np.array([0,0,0])
        if calibration._single_point_offset.is_valid:
            suggested_position = calibration._single_point_offset.pairing.stage_coordinate.to_list()
        
        stage_coordinate_str = cli.input("Where is stage {} located (X,Y,Z)?".format(calibration), str, ",".join(map(str, suggested_position)))
        stage_coordinate = list(map(float, stage_coordinate_str.split(",")))

        return np.array(stage_coordinate)

    def _detect_stage_collision(self):
        if any(m1.are_colliding(m2) for m1, m2 in combinations(self.stage_models.values(), 2)):
            self.stage_collision_text.text("STAGE-STAGE COLLISION DETECTED")
            self.stage_collision_text.color("red")
            self.stage_collision = True
        else:
            self.stage_collision_text.text("No collision detected")
            self.stage_collision_text.color("green")


    def _detect_chip_collision(self):
        if not self.chip_model:
            return

        for stage_model in self.stage_models.values():
            if self.chip_model.is_stage_colliding(stage_model):
                self.chip_collision_text.text("CHIP-STAGE COLLISION DETECTED")
                self.chip_collision_text.color("red")
                self.chip_collision = True
            else:
                self.chip_collision_text.text("No collision detected")
                self.chip_collision_text.color("green")