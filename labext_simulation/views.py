#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from abc import ABC, abstractmethod

from scipy.spatial.transform import Rotation
import numpy as np


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


class StageView(View):
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