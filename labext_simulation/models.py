#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod, abstractproperty
from typing import Type
import numpy as np
from vedo import Box, Plane, Spheres, Arrow, Cube

from LabExT.Wafer.Chip import Chip
from LabExT.Movement.MoverNew import Orientation
from labext_simulation.utils import get_all_view_files

from labext_simulation.views import AbsoluteView, RelativeView

import labext_simulation.cli as cli

class Model(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def mesh(self):
        pass

    @abstractmethod
    def set_simulation_parameters(self):
        pass


class WorldModel(Model):
    def __init__(self, x_size, y_size, z_size) -> None:
        self._mesh = Box((0,0,0), size=(-x_size,x_size,-y_size,y_size,-z_size,z_size), alpha=0)

    @property
    def mesh(self):
        return self._mesh


class StageModel(Model):
    
    FIBER_COLOR = "grey1"
    SAFETY_COLOR = "r7"

    X_AXIS_COLOR = "red"
    Y_AXIS_COLOR = "blue"
    Z_AXIS_COLOR = "green"

    AXIS_LENGTH = 1000

    @classmethod
    def build_list(cls):
        models = []
        while True:
            if not cli.confirm("Do you want to create a new stage model?", default=True):
                return models

            models.append(cls.build())
            cli.success("Successfully added new stage model.\n")

    @classmethod
    def build(cls):
        orientation = Orientation(cli.choice("How is the Stage oriented in space?", list(Orientation)))
        absolute_view = AbsoluteView.build(
            file=cli.choice("Select a transformation to be used to draw the Stage in World cooridnates", get_all_view_files()),
            orientation=orientation)
        relative_view = RelativeView.build()

        return cls(
            absolute_view=absolute_view,
            relative_view=relative_view,
            orientation=orientation,
            fiber_diameter=cli.input("Fiber Diameter", float, 125.0),
            fiber_length=cli.input("Fiber Length", float, 1e4))

    def __init__(
        self,
        absolute_view: Type[AbsoluteView],
        relative_view: Type[RelativeView],
        orientation: Orientation,
        fiber_diameter: float = 125.0,
        fiber_length: float = 1e4,
        safety_distance: float = 125.0) -> None:

        self.absolute_view = absolute_view
        self.relative_view = relative_view

        self.orientation = orientation
        self.fiber_diameter = fiber_diameter
        self.fiber_length = fiber_length
        self.safety_distance = safety_distance

        # Actual position of the stage in world cooridnates. 
        self.model_position = None
        self.view_position = None

        self.position = None

        # Meshes
        self._fiber_mesh = None
        self._safety_distance_mesh = None
        self._x_axis = None
        self._y_axis = None
        self._z_axis = None
        
    def __str__(self) -> str:
        return "{} Stage Model (Diameter: {}, Length: {})".format(self.orientation, self.fiber_diameter, self.fiber_length)

    @property
    def is_vertically_oriented(self):
        return self.orientation == Orientation.LEFT or self.orientation == Orientation.RIGHT

    def set_simulation_parameters(self, distance: float, model_position: list = None, view_position: list = None):
        self.safety_distance = distance
        self.model_position = model_position if model_position is not None else self.absolute_view.world_to_model((np.array(model_position)))
        self.view_position = view_position if view_position is not None else self.absolute_view.model_to_world(np.array(model_position))

    def mesh(self):
        if self.view_position is None:
            raise RuntimeError("Cannot create Mesh without view position")

        self._fiber_mesh = self._create_fiber_mesh()
        self._safety_distance_mesh = self._create_safety_distance_mesh()

        self._x_axis = self._create_axis(np.array([self.AXIS_LENGTH, 0, 0]), self.X_AXIS_COLOR)
        self._y_axis = self._create_axis(np.array([0, self.AXIS_LENGTH, 0]), self.Y_AXIS_COLOR)
        self._z_axis = self._create_axis(np.array([0, 0, self.AXIS_LENGTH]), self.Z_AXIS_COLOR)

        return self._fiber_mesh + self._safety_distance_mesh + self._x_axis + self._y_axis + self._z_axis


    def addPos(self, model_delta: np.ndarray):
        view_delta = self.relative_view.model_to_world(model_delta)

        self._safety_distance_mesh.addPos(*view_delta)
        self._fiber_mesh.addPos(*view_delta)
        self._x_axis.addPos(*view_delta)
        self._y_axis.addPos(*view_delta)
        self._z_axis.addPos(*view_delta)

        self.model_position += model_delta
        self.view_position += view_delta

    def pos(self, model_position: np.ndarray):
        view_position = self.absolute_view.model_to_world(model_position)

        self._safety_distance_mesh.pos(self._get_mesh_box_center(view_position))
        self._fiber_mesh.pos(self._get_mesh_box_center(view_position))
        self._x_axis.pos(view_position)
        self._y_axis.pos(view_position)
        self._z_axis.pos(view_position)

        self.model_position = model_position
        self.view_position = view_position

    def are_colliding(self, other) -> bool:
        if self._safety_distance_mesh is None or other._safety_distance_mesh is None:
            return False

        return self._safety_distance_mesh.triangulate().boolean("intersect", other._safety_distance_mesh.triangulate()).points().size > 0

    def _create_axis(self, unit_vector, color):
        return Arrow(self.view_position, self.view_position + self.relative_view.model_to_world(unit_vector), c=color)

    def _create_fiber_mesh(self):
        """
        Creates a box with height equal to the fiber length. The base is the diameter of the fiber times the length of the fiber to represent all possible angles of the fiber.
        """
        return Box(
            pos=self._get_mesh_box_center(self.view_position),
            width=self.fiber_diameter if self.is_vertically_oriented else self.fiber_length,
            length=self.fiber_length if self.is_vertically_oriented else self.fiber_diameter,
            height=self.fiber_length,
            c=self.FIBER_COLOR,
            alpha=0.6)

    def _create_safety_distance_mesh(self):
        """
        Creates a box that encloses the stage box with given safety distance in X and Y direction. 
        """
        diameter_safety = self.fiber_diameter + 2 * self.safety_distance
        length_safety = self.fiber_length + 2 * self.safety_distance
        return Box(
            pos=self._get_mesh_box_center(self.view_position),
            width=diameter_safety if self.is_vertically_oriented else length_safety,
            length=length_safety if self.is_vertically_oriented else diameter_safety,
            height=self.fiber_length,
            c=self.SAFETY_COLOR,
            alpha=0.4)


    def _get_mesh_box_center(self, view_position: np.ndarray) -> np.ndarray:
        """
        Returns the position of the fiber mesh.
        Its the position of stage shifted by half the fiber length in positive Z direction
        and shifted to X and Y direction depending on the stage orientation.
        """
        # Position of the fiber if not angle
        pos =  view_position + np.array([0,0,self.fiber_length / 2])
        if self.orientation == Orientation.LEFT:
            return pos + np.array([-self.fiber_length / 2 + self.fiber_diameter / 2, 0, 0])

        if self.orientation == Orientation.RIGHT:
            return pos + np.array([self.fiber_length / 2 - self.fiber_diameter / 2, 0, 0])

        if self.orientation == Orientation.BOTTOM:
            return pos + np.array([0, -self.fiber_length / 2 + self.fiber_diameter / 2, 0])

        if self.orientation == Orientation.TOP:
            return pos + np.array([0, self.fiber_length / 2 - self.fiber_diameter / 2, 0])


class ChipModel(Model):

    INPUT_COLOR = 'green7'
    OUTPUT_COLOR = 'red7'

    CHIP_COLOR = 'white'
    SAFETY_COLOR = "r7"

    @classmethod
    def build(cls, chip: Type[Chip]):
        if not chip:
            return None

        return cls(
            inputs=np.array([d.input_coordinate.to_list() for d in chip._devices.values()]),
            outputs=np.array([d.output_coordinate.to_list() for d in chip._devices.values()]),
            coupler_radius=cli.input("Coupler Radius in um", type=float, default=5),
            chip_width=cli.input("Chip size in um", type=float, default=10000))


    def __init__(self, inputs, outputs, safety_distance = 10, coupler_radius=5, chip_width=10000) -> None:
        self.inputs = inputs
        self.outputs = outputs

        self.chip_width = chip_width
        self.coupler_radius = coupler_radius
        self.safety_distance = safety_distance

        self.position = np.append(self.inputs, self.outputs, axis=0).mean(axis=0)

        self._chip_plane = None
        self._chip_inputs = None
        self._chip_outputs = None
        self._safety_distance_mesh = None

    def set_simulation_parameters(self, safety_distance: float):
        self.safety_distance = safety_distance

    def mesh(self):
        self._chip_plane = Plane(pos=self.position, normal=(0, 0, 1), s=(), sx=self.chip_width, sy=self.chip_width, c=self.CHIP_COLOR, alpha=1)
        self._chip_inputs = Spheres(self.inputs, c=self.INPUT_COLOR, alpha=1, r=self.coupler_radius)
        self._chip_outputs = Spheres(self.outputs, c=self.OUTPUT_COLOR, alpha=1, r=self.coupler_radius)
        self._safety_distance_mesh = self._create_safety_distance_mesh()

        return self._chip_plane + self._chip_inputs + self._chip_outputs + self._safety_distance_mesh

    def is_stage_colliding(self, stage_model: Type[StageModel]) -> bool:
        if self._safety_distance_mesh is None or stage_model._safety_distance_mesh is None:
            return False

        return self._safety_distance_mesh.triangulate().boolean("intersect", stage_model._safety_distance_mesh.triangulate()).points().size > 0

    def _create_safety_distance_mesh(self):
        """
        Creates a cube below the chip plane with given safety distance.
        """
        return Cube(
            pos=self.position + np.array([0,0,-self.safety_distance - self.chip_width / 2]),
            side=self.chip_width,
            c=self.SAFETY_COLOR,
            alpha=0.4)