"""
(*)~----------------------------------------------------------------------------------
 Pupil LSL Relay
 Copyright (C) 2012 Pupil Labs

 Distributed under the terms of the GNU Lesser General Public License (LGPL v3.0).
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
"""
import numpy as np
from pylsl import XMLElement


class Channel:
    def __init__(self, query, label, eye, metatype, unit, coordinate_system=None):
        self.label = label
        self.eye = eye
        self.metatype = metatype
        self.unit = unit
        self.coordinate_system = coordinate_system
        self.query = query

    def append_to(self, channels: XMLElement):
        chan = channels.append_child("channel")
        chan.append_child_value("label", self.label)
        chan.append_child_value("eye", self.eye)
        chan.append_child_value("type", self.metatype)
        chan.append_child_value("unit", self.unit)
        if self.coordinate_system:
            chan.append_child_value("coordinate_system", self.coordinate_system)


def confidence_channel():
    return Channel(
        query=extract_confidence,
        label="confidence",
        eye="both",
        metatype="Confidence",
        unit="normalized",
    )


def norm_pos_channels(coordinate_system="world"):
    return [
        Channel(
            query=make_extract_normpos(i),
            label="norm_pos_" + "xy"[i],
            eye="both",
            metatype="Screen" + "XY"[i],
            unit="normalized",
            coordinate_system=coordinate_system,
        )
        for i in range(2)
    ]


def gaze_point_3d_channels():
    return [
        Channel(
            query=make_extract_gaze_point_3d(i),
            label="gaze_point_3d_" + "xyz"[i],
            eye="both",
            metatype="Direction" + "XYZ"[i],
            unit="mm",
            coordinate_system="world",
        )
        for i in range(3)
    ]


def eye_center_channels():
    return [
        Channel(
            query=make_extract_eye_center_3d(eye, i),
            label="eye_center{}_3d_{}".format(eye, "xyz"[i]),
            eye=("right", "left")[eye],
            metatype="Position" + "XYZ"[i],
            unit="mm",
            coordinate_system="world",
        )
        for eye in range(2)
        for i in range(3)
    ]


def gaze_normal_channels():
    return [
        Channel(
            query=make_extract_gaze_normal_3d(eye, i),
            label="gaze_normal{}_{}".format(eye, "xyz"[i]),
            eye=("right", "left")[eye],
            metatype="Position" + "XYZ"[i],
            unit="mm",
            coordinate_system="world",
        )
        for eye in range(2)
        for i in range(3)
    ]


def diameter_2d_channels():
    return [
        Channel(
            query=make_extract_diameter_2d(eye),
            label="diameter{}_2d".format(eye),
            eye=("right", "left")[eye],
            metatype="Diameter",
            unit="pixels",
            coordinate_system="eye{}".format(eye),
        )
        for eye in range(2)
    ]


def diameter_3d_channels():
    return [
        Channel(
            query=make_extract_diameter_3d(eye),
            label="diameter{}_3d".format(eye),
            eye=("right", "left")[eye],
            metatype="Diameter",
            unit="mm",
            coordinate_system="eye{}".format(eye),
        )
        for eye in range(2)
    ]


def extract_confidence(gaze):
    return gaze["confidence"]


def make_extract_normpos(dim):
    return lambda gaze: gaze["norm_pos"][dim]


def make_extract_gaze_point_3d(dim):
    return (
        lambda gaze: gaze["gaze_point_3d"][dim] if "gaze_point_3d" in gaze else np.nan
    )


def make_extract_eye_center_3d(eye, dim):
    def extract_eye_center_3d(gaze):
        topic = gaze["topic"]
        if topic.endswith("3d.01."):
            if eye in gaze["eye_centers_3d"]:
                return gaze["eye_centers_3d"][eye][dim]
            elif str(eye) in gaze["eye_centers_3d"]:
                return gaze["eye_centers_3d"][str(eye)][dim]
            else:
                raise KeyError(f"Expected field `{eye}` in {gaze['eye_centers_3d']}")
        elif topic.endswith("3d.{}.".format(eye)):
            return gaze["eye_center_3d"][dim]
        else:
            return np.nan

    return extract_eye_center_3d


def make_extract_gaze_normal_3d(eye, dim):
    def extract_gaze_normal_3d(gaze):
        topic = gaze["topic"]
        if topic.endswith("3d.01."):
            if eye in gaze["gaze_normals_3d"]:
                return gaze["gaze_normals_3d"][eye][dim]
            elif str(eye) in gaze["gaze_normals_3d"]:
                return gaze["gaze_normals_3d"][str(eye)][dim]
            else:
                raise KeyError(f"Expected field `{eye}` in {gaze['gaze_normals_3d']}")
        elif topic.endswith("3d.{}.".format(eye)):
            return gaze["gaze_normal_3d"][dim]
        else:
            return np.nan

    return extract_gaze_normal_3d


def make_extract_diameter_2d(eye):
    def extract_diameter_2d(gaze):
        base_data = gaze["base_data"]
        for pupil in base_data:
            if pupil["id"] == eye:
                return pupil["diameter"]
        else:
            return np.nan

    return extract_diameter_2d


def make_extract_diameter_3d(eye):
    def extract_diameter_3d(gaze):
        base_data = gaze["base_data"]
        for pupil in base_data:
            if pupil["id"] == eye and "diameter_3d" in pupil:
                return pupil["diameter_3d"]
        else:
            return np.nan

    return extract_diameter_3d
