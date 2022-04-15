#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Type
from os import path, listdir

from LabExT.Movement.MoverNew import MoverNew, Orientation, DevicePort
from LabExT.Wafer.Chip import Chip

import src.CLI as cli

class MoverWizard:
    def __init__(self) -> None:
        cli.out("1. Create Mover Instance", underline=True)
        cli.out("Creating new Mover instance...")
        try:
            self._mover = MoverNew(experiment_manager=None)
        except Exception as ex:
            cli.out("Mover Instantiation failed: {}. Quitting...".format(ex), color=cli.ERROR_COLOR)
            return
        cli.out("Created new Mover instance! \n", color=cli.SUCCESS_COLOR)

        cli.out("2. Search for Stages", underline=True)
        if not self.search_for_stages():
            cli.out("No stage classes could be found. Please check if LabExT was installed correctly. Quitting...", color=cli.ERROR_COLOR)
            return

        cli.out("3. Connect and Assign Stages", underline=True)
        if not self.create_calibrations():
            cli.out("No stage was created. Please create at least one stage calibration. Quitting...", color=cli.ERROR_COLOR)
            return
        
        cli.out("4. Configure Mover", underline=True)
        if not self.configure_mover():
            return

    def search_for_stages(self) -> bool:
        cli.out("Looking for stage classes...")
        self._mover.reload_stage_classes()
        if len(self._mover.stage_classes) == 0:
            return False

        cli.out("Found {} stage classes!".format(len(self._mover.stage_classes)), color=cli.SUCCESS_COLOR)

        cli.out("Looking for stages attacted to the system...")
        self._mover.reload_stages()
        if len(self._mover.available_stages) == 0:
            return False

        cli.out("Found {} stages! \n".format(len(self._mover.available_stages)), color=cli.SUCCESS_COLOR)

        return True

    def create_calibrations(self) -> bool:
        for orientation in Orientation:
            if not cli.ask_yes_or_no(
                "Do you want to create a {} stage?".format(orientation),
                default=False):
                cli.out("Skipping {} stage...".format(orientation), color=cli.ERROR_COLOR)
                continue

            stage = self._select_a_available_stage()

            port_string = cli.ask_for_input(
                "Select a device port: {} ".format([p.name.lower() for p in DevicePort]))

            port = DevicePort[port_string.upper()]

            cli.out("Creating stage calibration for {} with orientation {} and port {}...".format(stage, orientation, port))
            try:
                calibration = self._mover.add_stage_calibration(stage, orientation, port)
            except RuntimeError as ex:
                cli.out("Creation failed: {}".format(str(ex)), color=cli.ERROR_COLOR)
                continue

            cli.out("Created new calibration!", color=cli.SUCCESS_COLOR)
            cli.out("Connecting to Stage...")
            try:
                calibration.connect_to_stage()
            except RuntimeError as ex:
                cli.out("Connection failed: {}".format(str(ex)), color=cli.ERROR_COLOR)
                continue
            cli.out("Successfully connected to stage! \n", color=cli.SUCCESS_COLOR)

        if self._mover.has_connected_stages:
            cli.out("Successfully connected {} stages! \n".format(len(self._mover.connected_stages)), color=cli.SUCCESS_COLOR)
            return True

        return False

    def configure_mover(self) -> bool:
        xy_speed = cli.ask_for_input("XY Speed in um/s", type=float, default=self._mover.DEFAULT_SPEED_XY)
        z_speed = cli.ask_for_input("Z Speed in um/s", type=float, default=self._mover.DEFAULT_SPEED_Z)
        xy_acceleration = cli.ask_for_input("XY Acceleration in um^2/s", type=float, default=self._mover.DEFAULT_ACCELERATION_XY)
        z_lift = cli.ask_for_input("Z channel up-movement in um", type=float, default=self._mover.DEFAULT_Z_LIFT)

        try:
            self._mover.speed_xy = xy_speed
            self._mover.speed_z = z_speed
            self._mover.acceleration_xy = xy_acceleration
            self._mover.z_lift = z_lift

            cli.out("Successfully configured Mover! \n", color=cli.SUCCESS_COLOR)

            return True
        except RuntimeError as ex:
            cli.out("Setting up mover failed: {}".format(str(ex)), color=cli.ERROR_COLOR)
            return False


    def _select_a_available_stage(self):
        cli.out("The following stages are available:")
        for idx, stage in enumerate(self._mover.available_stages):
            cli.out("\t [{}] {}".format(idx, stage))
        
        selected_id = cli.ask_for_input(
            "Select a stage: {} ".format([i for i in range(0,len(self._mover.available_stages))]),
            type=int)
        
        return self._mover.available_stages[selected_id]


class ChipWizard:
    def __init__(self) -> None:
        cli.out("1. Import Chip", underline=True)
        chips_folder = path.join(path.abspath(path.dirname(__file__)), "chips")
        chip_files = [f for f in listdir(chips_folder) if path.isfile(path.join(chips_folder, f))]

        if len(chip_files) == 0:
            cli.out("No chip files found. Please check the chips folder. Quitting...", color=cli.ERROR_COLOR)
            return None

        cli.out("The following chips are available:")
        for idx, chip_file in enumerate(chip_files):
            cli.out("\t [{}] {}".format(idx, chip_file))

        selected_id = cli.ask_for_input(
            "Select a chip file: {} ".format([i for i in range(0,len(chip_files))]),
            type=int)

        cli.out("Loading Chip file {}...".format(chip_files[selected_id]))
        try: 
            self._chip = Chip(path=path.join(chips_folder, chip_files[selected_id]))
            cli.out("Successfully imported chip {}! \n".format(chip_files[selected_id]), color=cli.SUCCESS_COLOR)
        except RuntimeError as ex:
            cli.out("Importing chip failed: {}".format(str(ex)), color=cli.ERROR_COLOR)
            self._chip = None