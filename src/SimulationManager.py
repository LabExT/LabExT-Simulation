#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import sleep
from typing import Type
from LabExT.Movement.MoverNew import MoverNew, Orientation, DevicePort

from src.CLI import CLI

class SimulationManager:
    def __init__(self) -> None:
        self.cli = CLI(self)

        self.mover: Type[MoverNew] = None

        self.__setup__()
        

    def __setup__(self):
        self.cli.out("--- WELCOME TO THE LABEXT MOVEMENT SIMULATION ---", bold=True)

        self.cli.out("Creating new Mover instance...")
        self.mover = MoverNew(experiment_manager=None)
        self.cli.out("Created new Mover instance!", color=self.cli.SUCCESS_COLOR)


        self.cli.out("Looking for stage classes...")
        self.mover.reload_stage_classes()
        if len(self.mover.available_stages) == 0:
            self.cli.out("No stage classes could be found. Please check if LabExT was installed correctly.", color=self.cli.ERROR_COLOR)
            return

        self.cli.out("Found {} stage classes!".format(len(self.mover.available_stages)), color=self.cli.SUCCESS_COLOR)

        self._setup_calibrations()
        if not self.mover.has_connected_stages:
            self.cli.out("No stage was created. Please create at least one stage calibration.", color=self.cli.ERROR_COLOR)
            return

        self.cli.out("Successfully connected {} stages! \n".format(len(self.mover.connected_stages)), color=self.cli.SUCCESS_COLOR)
        
        if not self._setup_mover_settings():
            return

        self.cli.out("Successfully configured mover! \n", color=self.cli.SUCCESS_COLOR)


    def _setup_calibrations(self):
        self.cli.out("1. Setup Stages", underline=True)

        for orientation in Orientation:
            if not self.cli.ask_yes_or_no(
                "Do you want to create a {} stage?".format(orientation),
                default=False):
                self.cli.out("Skipping {} stage...".format(orientation), color=self.cli.ERROR_COLOR)
                continue

            stage = self._select_a_available_stage()

            port_string = self.cli.ask_for_input(
                "Select a device port: {} ".format([p.name.lower() for p in DevicePort]))

            port = DevicePort[port_string.upper()]

            self.cli.out("Creating stage calibration for {} with orientation {} and port {}...".format(stage, orientation, port))
            try:
                calibration = self.mover.add_stage_calibration(stage, orientation, port)
            except RuntimeError as ex:
                self.cli.out("Creation failed: {}".format(str(ex)), color=self.cli.ERROR_COLOR)
                continue

            self.cli.out("Created new calibration!", color=self.cli.SUCCESS_COLOR)
            self.cli.out("Connecting to Stage...")
            try:
                calibration.connect_to_stage()
            except RuntimeError as ex:
                self.cli.out("Connection failed: {}".format(str(ex)), color=self.cli.ERROR_COLOR)
                continue
            self.cli.out("Successfully connected to stage! \n", color=self.cli.SUCCESS_COLOR)

            
    def _setup_mover_settings(self):
        self.cli.out("2. Setup Mover", underline=True)

        xy_speed = self.cli.ask_for_input("XY Speed in um/s", type=float, default=self.mover.DEFAULT_SPEED_XY)
        z_speed = self.cli.ask_for_input("Z Speed in um/s", type=float, default=self.mover.DEFAULT_SPEED_Z)
        xy_acceleration = self.cli.ask_for_input("XY Acceleration in um^2/s", type=float, default=self.mover.DEFAULT_ACCELERATION_XY)
        z_lift = self.cli.ask_for_input("Z channel up-movement in um", type=float, default=self.mover.DEFAULT_Z_LIFT)

        try:
            self.mover.speed_xy = xy_speed
            self.mover.speed_z = z_speed
            self.mover.acceleration_xy = xy_acceleration
            self.mover.z_lift = z_lift

            return True
        except RuntimeError as ex:
            self.cli.out("Setting up mover failed: {}".format(str(ex)), color=self.cli.ERROR_COLOR)
            return False

    def _select_a_available_stage(self):
        self.cli.out("The following stages are available:")
        for idx, stage in enumerate(self.mover.available_stages):
            self.cli.out("\t [{}] {}".format(idx, stage))
        
        selected_id = self.cli.ask_for_input(
            "Select a stage: {} ".format([i for i in range(0,len(self.mover.available_stages))]),
            type=int)
        
        return self.mover.available_stages[selected_id]
        
      