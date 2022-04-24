#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from time import time, sleep
from typing import Type

from LabExT.Movement.Stage import Stage
from LabExT.Movement.MotorProfiles import trapezoidal_velocity_profile_by_integration

from labext_simulation.simulation import Simulation, SimulationError, StageModel
import labext_simulation.cli as cli

import numpy as np
from vedo import ProgressBar

class SimulatedStage:

    def __init__(self, stage: Type[Stage], simulation: Type[Simulation], model: Type[StageModel]) -> None:
        self.stage: Type[Stage] = stage
        self.simulation: Type[Simulation] = simulation
        self.model: Type[StageModel] = model

        self._position: np.ndarray = None

    @property
    def position(self) -> list:
        return self._position.tolist() if self._position is not None else None

    def get_current_position(self) -> list:
        return self.position[:2] if self.position is not None else None

    def move_relative(self, x, y, z=0, wait_for_stopping: bool = True):
        if not wait_for_stopping:
            raise RuntimeError("Wait for stopping must be enabled in simulation")

        target = self._position + np.array([x,y,z])
        cli.out("\n\U0001F680 Simulating relative movement of {}".format(self), bold=True)
        cli.out("- Start Position {}, Target Position {}".format(self._position, target))

        t, p = self.__calculate_waypoints(target)
        cli.success("Starting simulation...")

        current_ts = 0.0
        total_render_time = 0.0
        pb = ProgressBar(0, t.size)
        for i in pb.range():
            render_start = time()
            self.model.addPos(p[i] - self.position)
            self.simulation.render_simulation_step()
            self._position = p[i]

            render_time = time() - render_start

            if self.simulation.parameters.realtime:
                sleep(max(t[i] - current_ts - render_time, 0))

            current_ts = t[i]
            total_render_time += render_time

            pb.print("[FRAME {} / {}] Move {} to X: {}, Y: {}, Z: {}".format(i, t.size, self, target[0], target[1], target[2]))

        cli.success("Stopping simulation...")
        cli.out("Average render time: {}".format(total_render_time / t.size))


    def move_absolute(self, x, y, z, wait_for_stopping: bool = True):
        if not wait_for_stopping:
            raise RuntimeError("Wait for stopping must be enabled in simulation")

        target = np.array([x,y,z])
        cli.out("\n\U0001F680 Simulating absolute movement of {}".format(self), bold=True)
        cli.out("- Start Position {}, Target Position {}".format(self._position, target))

        t, p = self.__calculate_waypoints(target)
        cli.success("Starting simulation...")

        current_ts = 0.0
        total_render_time = 0.0
        pb = ProgressBar(0, t.size)
        for i in pb.range():
            render_start = time()
            self.model.pos(p[i])
            self.simulation.render_simulation_step()
            self._position = p[i]
            render_time = time() - render_start

            if self.simulation.parameters.realtime:
                sleep(max(t[i] - current_ts - render_time, 0))

            current_ts = t[i]
            total_render_time += render_time

            pb.print("[FRAME {} / {}] Move {} to X: {}, Y: {}, Z: {}".format(i, t.size, self, target[0], target[1], target[2]))

        cli.success("Stopping simulation...")
        cli.out("Average render time: {}".format(total_render_time / t.size))

    #
    #   Simulate Movement
    #

    def __calculate_waypoints(self, target, dt_integration=1e-5):
        sampling_rate = self.simulation.parameters.sampling_rate
        
        if not self.simulation:
            raise RuntimeError("No Simulation defined for this stage.")

        cli.out("- Calculating Waypoints with {} integration and sub sampling rate {}".format(dt_integration, sampling_rate))

        tx, xs, _, _ = trapezoidal_velocity_profile_by_integration(self._position[0], target[0], self.get_speed_xy(), self.get_acceleration_xy())
        ty, ys, _, _ = trapezoidal_velocity_profile_by_integration(self._position[1], target[1], self.get_speed_xy(), self.get_acceleration_xy())
        tz, zs, _, _ = trapezoidal_velocity_profile_by_integration(self._position[2], target[2], self.get_speed_z(), self.get_acceleration_xy())

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

        return t, np.column_stack((x,y,z))

    #
    #   Delegate all other methods to stage
    #

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
    def get_status(self) -> tuple: return self.stage.get_status()
    
    def find_reference_mark(self): raise NotImplementedError
    def wiggle_z_axis_positioner(self): raise NotImplementedError
    def lift_stage(self, wait_for_stopping: bool = True): raise NotImplementedError
    def lower_stage(self, wait_for_stopping: bool = True): raise NotImplementedError
    def get_lift_distance(self): raise  NotImplementedError()
    def set_lift_distance(self, height): raise NotImplementedError