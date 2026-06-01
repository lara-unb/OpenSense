from __future__ import annotations
from dataclasses import dataclass
from scipy.spatial.transform import Rotation as R
import numpy as np


@dataclass
class Segment:
    """A body segment linked to one IMU in a kinematic chain.

    Stateless with respect to time: all geometry is computed on demand
    given a rotations dict and a timestep index.
    """
    label: str
    imu_label: str
    # joint_label: str
    # joint_rotation_labels: list[str]
    parent: Segment | None = None
    length: float = 1.0  # cm, used for visualisation
    initial_angle_deg: float | None = None  # calibration target angle at t=0
    parent_offset: np.ndarray | None = None  # attachment point in parent's local frame (cm); None → [parent.length, 0, 0]


    def get_rotation_global(self, rotations: dict, idx: int,
                            rot_seq: str = 'zyx') -> R:
        """Calibrated IMU rotation at timestep idx in the global frame.

        Calibration: finds the offset between the actual IMU orientation at
        t=0 and the desired initial pose, then applies that offset to every subsequent frame.
        """
        rot_series = rotations[self.imu_label]
        if self.initial_angle_deg is None:
            return rot_series[idx]
        rot_0 = rot_series[0]
        rot_target_0 = R.from_euler(
            rot_seq, [a * np.pi / 180 for a in self.initial_angle_deg]
        )
        rot_offset = rot_0.inv() * rot_target_0
        return rot_series[idx] * rot_offset

    def get_rotation_relative(self, rotations: dict, idx: int,
                              rot_seq: str = 'zyx') -> R:
        """Rotation relative to the parent segment.

        Returns the global rotation for root segments (no parent).
        """
        if self.parent is None:
            return self.get_rotation_global(rotations, idx, rot_seq)
        parent_global = self.parent.get_rotation_global(rotations, idx, rot_seq)
        self_global = self.get_rotation_global(rotations, idx, rot_seq)
        return parent_global.inv() * self_global

    def get_origin(self, rotations: dict, idx: int,
                   rot_seq: str = 'zyx') -> np.ndarray:
        """3D origin point of this segment in the global frame."""
        if self.parent is None:
            return np.zeros(3)
        parent_origin = self.parent.get_origin(rotations, idx, rot_seq)
        parent_rot = self.parent.get_rotation_global(rotations, idx, rot_seq)
        offset = self.parent_offset if self.parent_offset is not None else np.array([self.parent.length, 0, 0])
        return parent_origin + parent_rot.apply(offset)

    def get_end(self, rotations: dict, idx: int,
                rot_seq: str = 'zyx') -> np.ndarray:
        """3D end point of this segment in the global frame."""
        origin = self.get_origin(rotations, idx, rot_seq)
        rot = self.get_rotation_global(rotations, idx, rot_seq)
        return origin + rot.apply([self.length, 0, 0])

    def get_absolute_angle(self, rotations: dict, idx: int,
                        rot_seq: str = 'zyx') -> np.ndarray:
        """Euler angles (degrees) of the global rotation.

        For root segments (no parent), returns the global calibrated Euler angles.
        """
        return self.get_rotation_global(rotations, idx, rot_seq).as_euler(rot_seq, degrees=True)
    
    def get_joint_angle(self, rotations: dict, idx: int,
                        rot_seq: str = 'zyx') -> np.ndarray:
        """Euler angles (degrees) of the rotation relative to the parent segment.

        For root segments (no parent), returns the global calibrated Euler angles.
        Convention: R_rel = R_parent^{-1} * R_self, decomposed via rot_seq.
        """
        return self.get_rotation_relative(rotations, idx, rot_seq).as_euler(rot_seq, degrees=True)

    def get_axes(self, rotations: dict, idx: int,
                 rot_seq: str = 'zyx', axis_length: float = 10.0) -> dict:
        """Coordinate axis endpoints in the global frame.

        Returns a dict with keys 'origin', 'x', 'y', 'z', each an ndarray(3).
        axis_length controls the visual length of each axis arrow.
        """
        origin = self.get_origin(rotations, idx, rot_seq)
        rot = self.get_rotation_global(rotations, idx, rot_seq)
        return {
            'origin': origin,
            'x': origin + rot.apply([axis_length, 0, 0]),
            'y': origin + rot.apply([0, axis_length, 0]),
            'z': origin + rot.apply([0, 0, axis_length]),
        }
