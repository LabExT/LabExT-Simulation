#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import path, listdir
from typing import Type
from itertools import product

from LabExT.Wafer.Chip import Chip
from LabExT.Movement.Transformations import CoordinatePairing, StageCoordinate, ChipCoordinate, Axis, Direction
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
        "Run new Simulation": lambda self: self.run_simulation(),
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

        self.first_startup = True

        cli.success("Initialization completed. \n")

    def start(self):
        try:
            self.simulation = Simulation.build(self.mover)

            if self.first_startup:
                self.complete_setup()
                self.first_startup = False

            while True:
                cli.out("Simulation Menu", underline=True, bold=True, color='blue')
                action_key = cli.choice("What do you want to do?", self.ACTIONS.keys())
                self.ACTIONS.get(action_key, lambda s: None)(self)

        except KeyboardInterrupt:
            cli.out("\nExit LabExT Simulation.")
            return

    def run_simulation(self):
        sim_func = cli.choice("Run Simulation", [
            ("Show current environment", self.simulation.show_environment),
            ("Wiggle stage axis", self.simulation.wiggle_axes),
            ("Move to Device", self.simulation.move_to_device),
            ("Move to all Devices", self.simulation.move_to_all_devices),
            ("Back", lambda s: None)
        ])
        sim_func()

    def import_chip(self):
        """
        Import a chip by selecting a chip file.
        """
        if len(self.chip_files) == 0:
            cli.error("No chip files found to import.")
            return

        cli.out(f"{cli.ATOM} Import a Chip:", underline=True, bold=True)

        if self.chip and not cli.confirm("You have already loaded a chip. Do you want to replace it?"):
            return

        try:
            file = cli.choice("Select a chip file to import", choices=self.chip_files)
            self.chip = Chip(path=file, name=path.basename(file))
            self.simulation.chip = self.chip
            cli.success("Successfully imported chip! \n")
        except Exception as error:
            cli.error("Could not import chip: {} \n".format(error))
        

    def assign_stage(self):
        """
        Action to assign a new stage to the mover.
        """
        if len(self.mover.available_stages) == 0:
            cli.error("No available stages found.")
            return

        if not self.simulation.stage_models:
            cli.error("No simulated stages found. Please create a simulation env first.")
            return

        cli.out(f"{cli.ROBOT} Assign a stage to a simulation model:", underline=True, bold=True)

        stage = cli.choice("Select a real stage (connected to the computer):", self.mover.available_stages)
        model = cli.choice("Choose a Stage Model:", self.simulation.stage_models.values())
        port = DevicePort(cli.choice("Select a Port", list(DevicePort)))
        
        calibration = self.mover.add_stage_calibration(
            SimulatedStage(stage, self.simulation, model), 
            orientation=model.orientation,
            port=port)
        calibration.connect_to_stage()

        cli.success("Successfully assigned and connected stage! \n")        

        if cli.confirm("Do want to calibrate this stage?", default=True):
            self.calibrate_stage(calibration)



    def calibrate_stage(self, calibration: Type[Calibration] = None):
        """
        Action to calibrate a stage by defining cooridnate pairings.
        """
        if not self.mover.has_connected_stages:
            cli.error("There are no connected stages to calibrate.")
            return

        cli.out(f"{cli.TOOLS} Calibrate a stage:", underline=True, bold=True)

        if calibration is None:
            calibration = cli.choice("Select a stage to calibrate", self.mover.calibrations.values())

        self._calibrate_stage_axes(calibration)

        if cli.confirm("Do you want to do a calibration loaded from file?", default=True):
            self._load_calibration_from_file(calibration)
            cli.success("Successfully calibrated stage! \n")  
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
        
        cli.success("Successfully calibrated stage! \n")  

    def setup_mover(self):
        """
        Action to setup the mover settings.
        """
        cli.out(f"{cli.TOOLS} Configure Mover", bold=True, underline=True, color='blue')
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
        cli.out(f"{cli.HAT} Setup LabExT Mover and Stages", bold=True, underline=True, color='blue')
        cli.out("The following steps configure the LabExT Mover.\n")

        self.import_chip()
        assert self.chip is not None, "No chip imported!"

        while True:
            self.assign_stage()
            if not cli.confirm("Do you want to assign another stage?", default=True):
                break
        assert self.mover.has_connected_stages, "No connected stages!"

        cli.success("\U0001F680 Successfully completed setup! You are ready to go.\n")
        
    def _calibrate_stage_axes(self, calibration: Type[Calibration]):
        options = [(" ".join(map(str, o)), o) for o in product(Direction, Axis)]

        for chip_axis in Axis:
            direction, stage_axis = cli.choice("Positive {}-Chip-axis points to".format(chip_axis), options)
            calibration.update_axes_rotation(chip_axis, direction, stage_axis)
        
        if calibration.axes_rotation.is_valid:
            cli.success("Successfully updated Axes rotation! Wiggeling axes...")
            self.simulation.wiggle_all_axes(calibration)
            if cli.confirm("All good?", default=True):
                return

            self._calibrate_stage_axes(calibration)
        else:
            cli.error("Rotation invalid.")
            self._calibrate_stage_axes(calibration)

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
