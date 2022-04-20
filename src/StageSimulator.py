#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import time, sleep

from typing import Type, List
from LabExT.Movement.Stage import Stage
from LabExT.Movement.MotorProfiles import trapezoidal_velocity_profile_by_integration

import src.CLI as cli
from src.Models import StageModel
from src.Plotter import Plotter

import numpy as np
from vedo import ProgressBar

class StageSimulator(Stage):
    driver_loaded = True

    # Setup and initialization

    def __init__(self, stage):
        self.stage: Type[Stage] = stage

        self.plotters: List[Type[Plotter]] = None
        self.model: Type[StageModel] = None

        self._position = [0,0,0]


    def __register__simulation__(self, plotters, model):
        self.plotters = plotters
        self.model = model
        self._position = self.model.stage_position

    def __position_setter(self, position):
        self._position = position

    def get_status(self) -> tuple:
        return ("X status", "Y status", "Z status")

    @property
    def position(self) -> list:
        return self._position

    def get_current_position(self) -> list:
        return self.position[:2]


    def move_relative(self, x, y, z=0, wait_for_stopping: bool = True):
        if not wait_for_stopping:
            raise RuntimeError("Wait for stopping must be enabled in simulation")

        if not self.plotters or not self.model:
            raise RuntimeError("No Simulation defined for this stage.")

        self.__peform_simulated_movement([x,y,z], "relative")


    def move_absolute(self, x, y, z, wait_for_stopping: bool = True):
        if not wait_for_stopping:
            raise RuntimeError("Wait for stopping must be enabled in simulation")

        if not self.plotters or not self.model:
            raise RuntimeError("No Simulation defined for this stage.")

        self.__peform_simulated_movement([x,y,z], "absolute")


    def __peform_simulated_movement(self, target, movement_type, sampling_rate=1e4, dt_integration=1e-5):
        frames_per_second = 1 / (sampling_rate * dt_integration)
        target = np.array(target)

        cli.out("\n\U0001F680 Simulating {} movement of {}".format(movement_type, self), bold=True)
        target = target if movement_type == "absolute" else np.array(self.position) + target
        cli.out("- Start Position {}, Target Position {}".format(self.position, target))
        cli.out("- Calculating Waypoints with {} integration and sub sampling rate {} (Frames per second: {})".format(dt_integration, sampling_rate, frames_per_second))

        tx, xs, _, _ = trapezoidal_velocity_profile_by_integration(self.position[0], target[0], self.get_speed_xy(), self.get_acceleration_xy())
        ty, ys, _, _ = trapezoidal_velocity_profile_by_integration(self.position[1], target[1], self.get_speed_xy(), self.get_acceleration_xy())
        tz, zs, _, _ = trapezoidal_velocity_profile_by_integration(self.position[2], target[2], self.get_speed_z(), 20.0)

        if tx.size == 0 and ty.size == 0 and tz.size == 0:
            cli.error("All timepoint vectors are empty! Cannot execute movement!")
            return

        # Take longest time vector and subsample and include last element
        t_max = max(tx, ty, tz, key=lambda t: t.size)
        t = np.append(t_max[::int(sampling_rate)], t_max[-1])

        # Subsample all coordinate vectors and include last element
        x =  np.append(xs[::int(sampling_rate)], target[0] if xs.size == 0 else xs[-1])
        y =  np.append(ys[::int(sampling_rate)], target[1] if ys.size == 0 else ys[-1])
        z =  np.append(zs[::int(sampling_rate)], target[2] if zs.size == 0 else zs[-1])

        cli.out("- Calculated {} x-waypoints, {} y-waypoints, {} z-waypoints".format(x.size, y.size, z.size))
        cli.out("- Estimated finish time: {}".format(t[-1]))

        # Copy last element for all vectors which are smaller than the t vector
        x = np.pad(x, (0, t.size - x.size), mode='constant', constant_values=x[-1])
        y = np.pad(y, (0, t.size - y.size), mode='constant', constant_values=y[-1])
        z = np.pad(z, (0, t.size - z.size), mode='constant', constant_values=z[-1])

        cli.success("Starting simulation...")

        current_ts = 0.0
        total_render_time = 0.0
        pb = ProgressBar(0, t.size)
        for i in pb.range():
            render_start = time()
            self.model.pos(x=x[i], y=y[i], z=z[i])
            self.__position_setter([x[i], y[i], z[i]])
            for p in self.plotters:
                p.render()
           
            render_time = time() - render_start

            sleep(max(t[i] - current_ts - render_time, 0))

            current_ts = t[i]
            total_render_time += render_time

            pb.print("[FRAME {} / {}] Move {} to X: {}, Y: {}, Z: {}".format(i, t.size, self, target[0], target[1], target[2]))

        cli.success("Stopping simulation...")
        cli.out("Average render time: {}".format(total_render_time / t.size))
        cli.out("Stage position {}, Mesh position {}, MSE : {}".format(
            self.position,
            self.model.stage_position,
            (np.square(self.position - self.model.stage_position)).mean()))

       
    def __str__(self) -> str: return self.stage.__str__()
    @property
    def address_string(self) -> str: return self.stage.address_string

    @property
    def connected(self) -> bool: return self.stage.connected

    def connect(self) -> bool: return self.stage.connect()
    def disconnect(self): self.stage.disconnect()
    def set_speed_xy(self, umps: float): self.stage.set_speed_xy(umps)
    def set_speed_z(self, umps: float): self.stage.set_speed_z(umps)
    def get_speed_xy(self) -> float: return self.stage.get_speed_xy()
    def get_speed_z(self): return self.stage.get_speed_z()
    def set_acceleration_xy(self, umps2): self.stage.set_acceleration_xy(umps2)
    def get_acceleration_xy(self) -> float: return self.stage.get_acceleration_xy()

    
    def find_reference_mark(self): raise NotImplementedError
    def wiggle_z_axis_positioner(self): raise NotImplementedError
    def lift_stage(self, wait_for_stopping: bool = True): raise NotImplementedError
    def lower_stage(self, wait_for_stopping: bool = True): raise NotImplementedError
    def get_lift_distance(self): raise  NotImplementedError()
    def set_lift_distance(self, height): raise NotImplementedError

