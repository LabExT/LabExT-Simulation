#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod, abstractproperty
from operator import add
from functools import reduce
from turtle import position
from typing import Type
import numpy as np
from vedo import Box, Plane, Sphere, Spheres

from LabExT.Wafer.Chip import Chip
from LabExT.Movement.Calibration import Calibration, Transformation, ChipCoordinate
from LabExT.Movement.MoverNew import Orientation
from labext_simulation.utils import get_all_view_files

from labext_simulation.views import StageView

import labext_simulation.cli as cli

class Model(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractproperty
    def mesh(self):
        pass


class WorldModel(Model):
    def __init__(self, x_size, y_size, z_size) -> None:
        self._mesh = Box((0,0,0), size=(-x_size,x_size,-y_size,y_size,-z_size,z_size), alpha=0)

    @property
    def mesh(self):
        return self._mesh


class StageModel(Model):
    
    FIBER_COLOR = "g1"
    ANGLE_COLOR = "b7"
    SAFETY_COLOR = "r7"

    @classmethod
    def build(cls, calibration: Type[Calibration]):
        stage_view = StageView.build(
            file=cli.choice("Select a transformation file", get_all_view_files()),
            orientation=calibration.orientation)

        suggested_position = None
        if calibration.single_point_transformation.is_valid:
            suggested_position = calibration.single_point_transformation._stage_coordinate

        if suggested_position and cli.confirm("Do you want to create a model for {} at Stage-Pos {}?".format(calibration, suggested_position), default=True):
            return cls(stage_view, calibration.orientation, suggested_position.to_list())

        return cls(
            stage_view,
            calibration.orientation,
            model_position=list(map(float, cli.input("Stage Coordinate (X,Y,Z)", type=str, default="0,0,0").split(","))))

    def __init__(
        self,
        view: Type[StageView],
        orientation: Orientation,
        model_position: list,
        fiber_diameter: float = 125.0,
        fiber_length: float = 1e4,
        safety_distance: float = 125.0) -> None:
        self.view = view

        self.orientation = orientation
        self.fiber_diameter = fiber_diameter
        self.fiber_length = fiber_length
        self.safety_distance = safety_distance

        # Actual position of the stage in world cooridnates. 
        self.model_position = model_position
        self.position = self.view.model_to_world(np.array(model_position))

        # Create meshes
        self._tip_point = Sphere(self.position, r=10, c="black")
        self._fiber_mesh = self._create_fiber_mesh()
        self._safety_distance_mesh = self._create_safety_distance_mesh()

        # Combine meshes
        self._mesh = self._tip_point + self._fiber_mesh + self._safety_distance_mesh

    @property
    def mesh(self):
        return self._mesh

    @property
    def mesh_position(self):
        """
        Returns the position of the fiber mesh.
        Its the position of stage shifted by half the fiber length in positive Z direction
        and shifted to X and Y direction depending on the stage orientation.
        """
        # Position of the fiber if not angle
        position = self.position + np.array([0,0,self.fiber_length / 2])
        if self.orientation == Orientation.LEFT:
            return position + np.array([-self.fiber_length / 2 + self.fiber_diameter / 2, 0, 0])

        if self.orientation == Orientation.RIGHT:
            return position + np.array([self.fiber_length / 2 + self.fiber_diameter / 2, 0, 0])

        if self.orientation == Orientation.BOTTOM:
            return position + np.array([0, -self.fiber_length / 2 + self.fiber_diameter / 2, 0])

        if self.orientation == Orientation.TOP:
            return position + np.array([0, self.fiber_length / 2 + self.fiber_diameter / 2, 0])

    @property
    def is_vertically_oriented(self):
        return self.orientation == Orientation.LEFT or self.orientation == Orientation.RIGHT


    def pos(self, x=None, y=None, z=None):
        self.position = self.view.model_to_world(np.array([
            x if x else self.position[0],
            y if y else self.position[1],
            z if z else self.position[2],
        ]))
        self._tip_point.pos(self.position)
        self._fiber_mesh.pos(self.mesh_position)
        self._safety_distance_mesh.pos(self.mesh_position)

    def collide(self, other):
        return self._safety_distance_mesh.triangulate().boolean("intersect", other._safety_distance_mesh.triangulate())

    def _create_fiber_mesh(self):
        """
        Creates a box with height equal to the fiber length. The base is the diameter of the fiber times the length of the fiber to represent all possible angles of the fiber.
        """
        return Box(
            pos=self.mesh_position,
            width=self.fiber_diameter if self.is_vertically_oriented else self.fiber_length,
            length=self.fiber_length if self.is_vertically_oriented else self.fiber_diameter,
            height=self.fiber_length,
            c=self.FIBER_COLOR,
            alpha=0.8)

    def _create_safety_distance_mesh(self):
        """
        Creates a box that encloses the stage box with given safety distance in X and Y direction. 
        """
        diameter_safety = self.fiber_diameter + 2 * self.safety_distance
        length_safety = self.fiber_length + 2 * self.safety_distance
        return Box(
            pos=self.mesh_position,
            width=diameter_safety if self.is_vertically_oriented else length_safety,
            length=length_safety if self.is_vertically_oriented else diameter_safety,
            height=self.fiber_length,
            c=self.SAFETY_COLOR,
            alpha=0.2)


class ChipModel(Model):

    INPUT_COLOR = 'green7'
    OUTPUT_COLOR = 'red7'

    CHIP_COLOR = 'white'

    @classmethod
    def build(cls, chip: Type[Chip]):
        if not chip:
            return None

        return cls(
            inputs=np.array([d.input_coordinate.to_list() for d in chip._devices.values()]),
            outputs=np.array([d.output_coordinate.to_list() for d in chip._devices.values()]),
            coupler_radius=cli.input("Coupler Radius in um", type=float, default=5),
            chip_width=cli.input("Chip size in um", type=float, default=10000))


    def __init__(self, inputs, outputs, coupler_radius=5, chip_width=10000) -> None:
        self.inputs = inputs
        self.outputs = outputs

        self.coupler_radius = coupler_radius

        position = np.append(self.inputs, self.outputs, axis=0).mean(axis=0)

        self._chip_plane = Plane(pos=position, normal=(0, 0, 1), s=(), sx=chip_width, sy=chip_width, c=self.CHIP_COLOR, alpha=1)
        self._chip_inputs = Spheres(self.inputs, c=self.INPUT_COLOR, alpha=1, r=self.coupler_radius)
        self._chip_outputs = Spheres(self.outputs, c=self.OUTPUT_COLOR, alpha=1, r=self.coupler_radius)

        self._mesh = self._chip_plane + self._chip_inputs + self._chip_outputs

    @property
    def mesh(self):
        return self._mesh