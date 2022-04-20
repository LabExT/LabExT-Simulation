#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Type
from enum import Enum, auto

from inquirer import Text, List, Confirm, prompt

import src.CLI as cli
from src.StageSimulator import StageSimulator

from src.Simulation import Simulation

from LabExT.Movement.Transformations import StageCoordinate, CoordinatePairing
from LabExT.Movement.MoverNew import MoverNew, State, Orientation, DevicePort, Calibration
from LabExT.Wafer.Chip import Chip


MARCO_POINTS = [
    {"device_id": 100, "stage_cooridnate": [23236.35, -7888.67, 18956.06]},
    {"device_id": 113, "stage_cooridnate": [23744.60, -9172.55, 18956.10]},
    {"device_id": 142, "stage_cooridnate": [25846.07, -10348.82, 18955.11]},
    {"device_id": 132, "stage_cooridnate": [25837.80, -7721.47, 18972.08]}
]

class Action(Enum):
    CONFIGURE_STAGE = auto()
    IMPORT_CHIP = auto()
    SETUP_MOVER = auto()

    NEW_SIMULATION = auto()

    EXIT = auto()

class SimulationManager:
    def __init__(self, chip=None) -> None:
        self.mover = MoverNew(experiment_manager=None)
        self.chip = chip

        self.__start__()


    def __start__(self):
        while True:
            cli.out("\n----- SIMULATION MENU ----", bold=True)
            cli.out("Current Mover state: {}".format(self.mover.state))
            cli.out("Imported Chip: {}".format(self.chip))

            action = cli.ask_for_action("Choose an action", [
                ('Configure a new stage', Action.CONFIGURE_STAGE),
                ('Import Chip', Action.IMPORT_CHIP),
                ('Configure Mover', Action.SETUP_MOVER),
                ('Start new Simulation', Action.NEW_SIMULATION),
                ('Exit', Action.EXIT)
            ])

            if action == Action.CONFIGURE_STAGE:
                self._configure_stage()
            elif action == Action.IMPORT_CHIP:
                self._import_chip()
            elif action == Action.SETUP_MOVER:
                self._configure_mover()
            elif action == Action.NEW_SIMULATION:
                self._new_simulation()
            elif action == Action.EXIT:
                return
            else:
                raise RuntimeError("Unsupported action {}".format(action))


    def _new_simulation(self):
        self.simulation = Simulation(self.mover, self.chip)

        for device in self.chip._devices.values():
            self.simulation.move_to_device(device)

    def _configure_stage(self):
        stage_setup = cli.setup_new_stage(self.mover.available_stages, list(Orientation), list(DevicePort))
    
        try:
            calibration = self.mover.add_stage_calibration(
                StageSimulator(stage_setup['stage']),
                Orientation(stage_setup['orientation']),
                DevicePort(stage_setup['port']))
            calibration.connect_to_stage()
        except Exception as error:
            cli.error("Setup failed: {}".format(error))

        cli.success("Successfully configured and connected: {}".format(calibration))

        if cli.confirm("Do you want to calibrate this stage?", default=True):
            self._calibrate_stage(calibration)

        if cli.confirm("Do you want to configure another stage?", default=False):
            self._configure_stage()

    def _configure_mover(self):
        mover_settings = cli.setup_mover()
        try:
            self.mover.speed_xy = mover_settings['speed_xy']
            self.mover.speed_z = mover_settings['speed_z']
            self.mover.acceleration_xy = mover_settings['acceleration_xy']
            self.mover.z_lift = mover_settings['z_lift']

            cli.success("Successfully configured Mover! \n")
        except RuntimeError as ex:
            cli.error("Setting up mover failed: {}".format(str(ex)))
        

    def _calibrate_stage(self, calibration: Type[Calibration]):
        cli.out("\n{} Calibration".format(calibration), bold=True)

        for fixed_pairings in MARCO_POINTS:
            pairing = self._new_pairing(calibration, fixed_pairings["device_id"], fixed_pairings["stage_cooridnate"])
            if not pairing:
                return

            if not calibration.single_point_transformation.is_valid: 
                calibration.update_single_point_transformation(pairing)
            calibration.update_full_transformation(pairing)

            cli.success("New Calibration state: {}".format(calibration.state))
            if not cli.confirm("Do you want to define more pairings?", default=True):
                return
        

    def _new_pairing(self, calibration, device_id=None, stage_coordinate=[]) -> Type[CoordinatePairing]:
        cli.out("Define a new pairing")
        paring_answers = prompt([
            Text('device_id', "Device ID", default=device_id),
            Text('stage_coordinate', "Stage Cooridnate (X, Y, Z)", default=",".join(map(str, stage_coordinate))),
        ])
        device = self.chip._devices.get(int(paring_answers['device_id']))
        if not device:
            cli.error("Could not find device {}".format(paring_answers['device_id']))
            return None

        return CoordinatePairing(
            calibration=calibration,
            stage_coordinate=StageCoordinate(*list(map(float, paring_answers['stage_coordinate'].split(",")))),
            device=device,
            chip_coordinate=device.input_coordinate if calibration.is_input_stage else device.output_coordinate
        )

    def _import_chip(self):      
        if self.chip and not cli.confirm("A chip is defined. Do you want to replace it?", default=False):
            return

        chip_path = cli.setup_new_chip()
        try:
            self.chip = Chip(chip_path)
        except Exception as error:
            cli.error("Import failed: {}".format(error))
            return

        cli.success("Successfully imported chip!")
        
        
      