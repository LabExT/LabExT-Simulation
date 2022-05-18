#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from abc import ABC, abstractmethod

from scipy.spatial.transform import Rotation
import numpy as np

import labext_simulation.cli as cli

class View(ABC):
    """
    A view defines a mapping between the world coordinates and the model coordinates.
    """
    @abstractmethod
    def model_to_world(self, model_coordinates: np.ndarray) -> np.ndarray:
        """
        Transforms a model coordinate to a world coordinate.
        """
        pass

    @abstractmethod
    def world_to_model(self, world_coordinates: np.ndarray) -> np.ndarray:
        """
        Transforms a world coordinate to a model coordinate.
        """
        pass


class RelativeView(View):
    """
    A Stage view for relative drawings.
    """
    @classmethod
    def build(cls):
        x_unit = list(map(float, cli.input("X-Axis Unit vector", str, "1,0,0").split(",")))
        y_unit = list(map(float, cli.input("Y-Axis Unit vector", str, "0,1,0").split(",")))
        z_unit = list(map(float, cli.input("Z-Axis Unit vector", str, "0,0,1").split(",")))

        return cls(np.array(x_unit), np.array(y_unit), np.array(z_unit))

    
    def __init__(
        self,
        x_unit: np.ndarray = np.array([1,0,0]),
        y_unit: np.ndarray = np.array([0,1,0]),
        z_unit: np.ndarray = np.array([0,0,1])
    ) -> None:
        self.rotation = Rotation.from_matrix(np.column_stack((x_unit, y_unit, z_unit)))


    def model_to_world(self, model_coordinates: np.ndarray) -> np.ndarray:
        """
        Transforms a model coordinate to a world coordinate.
        """
        return self.rotation.apply(model_coordinates)


    def world_to_model(self, world_coordinates: np.ndarray) -> np.ndarray:
        """
        Transforms a world coordinate to a model coordinate.
        """
        return self.rotation.apply(world_coordinates, inverse=True)
        

class AbsoluteView(View):
    """
    A Stage view for a patricular stage based on a particular chip dimension.
    """
    @classmethod
    def build(cls, file, orientation):
        with open(file) as f:
            data = json.load(f).get(orientation.name.lower())
            if data is None:
                raise RuntimeError("No transformation defined for {} stage of chip {}".format(orientation, file))
            
        return cls(
            model_coordinates=np.array([p.get("stage_coordinate") for p in data]),
            world_coordinates=np.array([p.get("chip_coordinate") for p in data]))


    def __init__(self, model_coordinates: np.ndarray, world_coordinates: np.ndarray) -> None:
        self.model_coordinates = model_coordinates
        self.world_coordinates = world_coordinates
        
        self.world_offset = self.world_coordinates.mean(axis=0)
        self.model_offset = self.model_coordinates.mean(axis=0)

        # Create Rotation with centered vectors
        self.rotation, self._rmsd = Rotation.align_vectors(
            (self.world_coordinates - self.world_offset),
            (self.model_coordinates - self.model_offset))

    def model_to_world(self, model_coordinates: np.ndarray) -> np.ndarray:
        """
        Transforms a model coordinate to a world coordinate.
        """
        return self.rotation.apply(np.array(model_coordinates) - self.model_offset) + self.world_offset


    def world_to_model(self, world_coordinates: np.ndarray) -> np.ndarray:
        """
        Transforms a world coordinate to a model coordinate.
        """
        return self.rotation.apply(np.array(world_coordinates) - self.world_offset, inverse=True) + self.model_offset