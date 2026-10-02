"""Calibrated URDF forward kinematics for checking sampled paths in base/TCP."""
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation


class Kinematics:
    def __init__(self, xml, offset):
        self.joints = {}
        for joint in ET.fromstring(xml).findall("joint"):
            origin = joint.find("origin")
            xyz = [float(x) for x in origin.get("xyz", "0 0 0").split()] if origin is not None else [0, 0, 0]
            rpy = [float(x) for x in origin.get("rpy", "0 0 0").split()] if origin is not None else [0, 0, 0]
            transform = np.eye(4)
            transform[:3, :3] = Rotation.from_euler("xyz", rpy).as_matrix()
            transform[:3, 3] = xyz
            axis = joint.find("axis")
            self.joints[joint.find("child").get("link")] = (
                joint.find("parent").get("link"), joint.get("name"), joint.get("type"),
                transform, np.array([float(x) for x in axis.get("xyz", "1 0 0").split()]) if axis is not None else np.array([1., 0., 0.]))
        self.offset = np.eye(4)
        self.offset[:3, 3] = offset[:3]
        self.offset[:3, :3] = Rotation.from_rotvec(offset[3:]).as_matrix()
        self.base_inverse = np.linalg.inv(self.world("base", {}))

    def world(self, link, positions):
        if link not in self.joints:
            return np.eye(4)
        parent, name, kind, origin, axis = self.joints[link]
        motion = np.eye(4)
        if kind in ("revolute", "continuous"):
            motion[:3, :3] = Rotation.from_rotvec(axis * positions[name]).as_matrix()
        elif kind != "fixed":
            raise ValueError("Unsupported kinematics joint type")
        return self.world(parent, positions) @ origin @ motion

    def tcp(self, names, positions):
        return self.base_inverse @ self.world("tool0", dict(zip(names, positions))) @ self.offset
