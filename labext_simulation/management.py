#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import path, listdir
from typing import Type

from LabExT.Wafer.Chip import Chip
from LabExT.Movement.Transformations import CoordinatePairing, StageCoordinate, ChipCoordinate
from LabExT.Movement.MoverNew import MoverNew, Calibration, Orientation, DevicePort

import labext_simulation.cli as cli
from labext_simulation.SimulatedStage import SimulatedStage
from labext_simulation.simulation import Simulation
from labext_simulation.utils import get_all_transformations

class SimulationManager:

    ACTIONS = {
        "Import a chip": lambda self: self.import_chip(),
        "Assign a new stage": lambda self: self.assign_stage(),
        "Calibrate stages": lambda self: self.calibrate_stage(),
        "Setup Mover settings": lambda self: self.setup_mover(),
        "Start new Simulation": lambda self: self.new_simulation(),
        "Exit the Simulation": lambda self: self.exit()
    }

    def __init__(self, chips_folder_path, views_folder_path) -> None:
        cli.out("--- WELCOME TO THE LABEXT MOVEMENT SIMULATION ---", bold=True, color='yellow')

        self.chip_files = _get_all_file_of_folder(chips_folder_path)
        self.view_files = _get_all_file_of_folder(views_folder_path)

        cli.out("Found {} chip files in folder {}.".format(len(self.chip_files), chips_folder_path))
        cli.out("Found {} view files in folder {}.".format(len(self.view_files), views_folder_path))

        self.mover = MoverNew(experiment_manager=None)
        self.chip = None
        self.simulation = None

        self.first_startup = True

        cli.success("Initialization completed. \n")

    def start(self):
        if self.first_startup and cli.confirm("Welcome! Want to do a guided setup?", default=True):
            self.complete_setup()

        try:
            while True:
                cli.out("Simulation Menu", underline=True, bold=True, color='blue')
                action_key = cli.choice("What do you want to do?", self.ACTIONS.keys())
                self.ACTIONS.get(action_key, lambda s: None)(self)
        except KeyboardInterrupt:
            cli.out("\nExit LabExT Simulation.")


    def new_simulation(self):
        simulation = Simulation(self.mover, self.chip)
        simulation.move_to_all_devices()

    def import_chip(self):
        """
        Import a chip by selecting a chip file.
        """
        if len(self.chip_files) == 0:
            cli.error("No chip files found to import.")
            return

        if self.chip and not cli.confirm("You have already loaded a chip. Do you want to replace it?"):
            return

        try:
            file = cli.choice("Select a chip file to import", choices=self.chip_files)
            self.chip = Chip(path=file, name=path.basename(file))
            cli.success("Successfully imported chip!")
        except Exception as error:
            cli.error("Could not import chip: {}".format(error))
        

    def assign_stage(self):
        """
        Action to assign a new stage to the mover.
        """
        if len(self.mover.available_stages) == 0:
            cli.error("No available stages found.")

        stage = cli.choice(
            "Which stage should be configured?",
            self.mover.available_stages)
        orientation = cli.choice(
            "What orientation should the stage have?",
            list(Orientation))
        port = cli.choice(
            "What port should the stage have?",
            list(DevicePort))

        c = self.mover.add_stage_calibration(
            SimulatedStage(stage), 
            Orientation(orientation),
            DevicePort(port))
        c.connect_to_stage()

        if cli.confirm("Do want to calibrate this stage?", default=True):
            self.calibrate_stage(c)



    def calibrate_stage(self, calibration: Type[Calibration] = None):
        """
        Action to calibrate a stage by defining cooridnate pairings.
        """
        if not self.mover.has_connected_stages:
            cli.error("There are no connected stages to calibrate.")
            return

        if calibration is None:
            calibration = cli.choice("Select a stage to calibrate", self.mover.calibrations.values())

        if cli.confirm("Do you want to do a calibration loaded from file?", default=True):
            self._load_calibration_from_file(calibration)
            return

        while True:
            pairing = self._create_a_new_pairing(calibration)
            if pairing:
                try:
                    if not calibration.single_point_transformation.is_valid: 
                        calibration.update_single_point_transformation(pairing)
                    calibration.update_full_transformation(pairing)
                except Exception as error:
                    cli.error("Could not update transformation: {}".format(error))
                    return

                cli.success("New Calibration state: {}".format(calibration.state))
            if not cli.confirm("Do you want to define more pairings?", default=True):
                break

    def setup_mover(self):
        """
        Action to setup the mover settings.
        """
        try:
            self.mover.speed_xy = cli.input("Speed XY in um/s", type=float, default=self.mover.DEFAULT_SPEED_XY)
            self.mover.speed_z = cli.input("Speed Z in um/s", type=float, default=self.mover.DEFAULT_SPEED_Z)
            self.mover.acceleration_xy = cli.input("Acceleration XY in um^2/s", type=float, default=self.mover.DEFAULT_ACCELERATION_XY)
            self.mover.z_lift = cli.input("Z channel up-movement in um", type=float, default=self.mover.DEFAULT_Z_LIFT)
            cli.success("Successfully configured Mover! \n")
        except RuntimeError as ex:
            cli.error("Setting up mover failed: {}".format(ex))


    def exit(self):
        """
        Exit Simulation Manager.
        """
        raise KeyboardInterrupt


    def complete_setup(self):
        """
        Action to setup end-to-end.
        """
        cli.out("1. Import a Chip", underline=True, color="blue")
        self.import_chip()
        assert self.chip is not None, "No chip imported!"

        cli.out("2. Assign Stages", underline=True, color="blue")
        while True:
            self.assign_stage()
            if not cli.confirm("Do you want to assign another stage?", default=True):
                break
        assert self.mover.has_connected_stages, "No connected stages!"

        cli.out("3. Setup Mover Settings", underline=True, color="blue")
        self.setup_mover()

        cli.success("\U0001F680 Successfully completed setup! You are ready to go.\n")
        


    def _create_a_new_pairing(self, calibration) -> Type[CoordinatePairing]:
        """
        Create a new cooridnate pairing.
        """
        if not self.chip:
            cli.error("No chip imported! Please import a chip first.")
            return

        cli.out("\nCreate a new coordinate pairing", underline=True)
        try:
            device = self.chip._devices[cli.input("Device ID", type=int)]
            return CoordinatePairing(
                calibration=calibration,
                stage_coordinate=StageCoordinate(
                    *list(map(float, cli.input("Stage Coordinate (X,Y,Z)", type=str).split(",")))),
                device=device,
                chip_coordinate=device.input_coordinate if calibration.is_input_stage else device.output_coordinate)
        except KeyError:
            cli.error("Could not find selected device.")
        except ValueError:
            cli.error("Please use floating point numbers for the coordinates.")


    def _load_calibration_from_file(self, calibration: Type[Calibration]):
        saved_trafos = get_all_transformations()
        if len(saved_trafos) == 0:
            cli.error("No saved calibrations found.")
            return

        selected_id = cli.choice("Select a calibration file", [(c.get("chipName"), idx) for idx, c in enumerate(saved_trafos)])
        selected_trafo = saved_trafos[selected_id].get(calibration.orientation.name.lower())
        if selected_trafo is None:
            cli.error("For the given orientation is no calibration available")
            return
        
        chip_coordinates = selected_trafo.get("chipCoordinates")
        stage_coordinates = selected_trafo.get("stageCoordinates")

        fix_point_id = cli.choice("Select a single point", [(str(c), idx) for idx, c in enumerate(chip_coordinates)])
        
        calibration.update_single_point_transformation(CoordinatePairing(
            calibration=calibration,
            stage_coordinate=StageCoordinate.from_list(stage_coordinates[fix_point_id]),
            device=object(),
            chip_coordinate=ChipCoordinate.from_list(chip_coordinates[fix_point_id])))

        for idx, chip_coordinate in enumerate(chip_coordinates):
            calibration.update_full_transformation(CoordinatePairing(
                calibration=calibration,
                stage_coordinate=StageCoordinate.from_list(stage_coordinates[idx]),
                device=object(),
                chip_coordinate=ChipCoordinate.from_list(chip_coordinate)))

def start_simulation_manager(chips_folder_path = None, views_folder_path = None):
    manager = SimulationManager(chips_folder_path, views_folder_path)
    manager.start()


def _get_all_file_of_folder(folder):
    if not path.exists(folder):
        return []

    return [path.join(folder, f) for f in listdir(folder) if path.isfile(path.join(folder, f))]
