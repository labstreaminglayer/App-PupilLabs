"""
(*)~----------------------------------------------------------------------------------
 Pupil LSL Relay
 Copyright (C) 2012-2016 Pupil Labs

 Distributed under the terms of the GNU Lesser General Public License (LGPL v3.0).
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
"""

from time import sleep
import logging

import numpy as np
import pylsl as lsl

from plugin import Plugin
from pyglui import ui


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Pupil_LSL_Relay(Plugin):
    """Plugin to relay Pupil Capture data to LSL"""

    icon_chr = "LR"

    def __init__(self, g_pool):
        super().__init__(g_pool)

    def init_ui(self):
        """Initializes sidebar menu"""
        self.add_menu()
        self.menu.label = "Pupil LSL Relay"

    def deinit_ui(self):
        self.remove_menu()

    def cleanup(self):
        """gets called when the plugin get terminated.
           This happens either voluntarily or forced.
        """
        pass

    @staticmethod
    def _append_acquisition_info(streaminfo):
        """Appends acquisition information to stream description"""
        acquisition = streaminfo.desc().append_child("acquisition")
        acquisition.append_child_value("manufacturer", "Pupil Labs")
        acquisition.append_child_value("source", "Pupil LSL Relay Plugin")
        acquisition.append_child_value("model", "2")

    def _create_primitive_lsl_outlet(self):
        """Create 5 channel primitive data outlet"""
        stream_info = lsl.StreamInfo(
            name="pupil_capture",
            type="Gaze",
            channel_count=5,
            channel_format=lsl.cf_double64,
        )
        self._append_channel_info(
            stream_info,
            ("diameter", "confidence", "timestamp", "norm_pos_x", "norm_pos_y"),
        )
        self._append_acquisition_info(stream_info)
        return lsl.StreamOutlet(stream_info)

    @staticmethod
    def _append_channel_info(streaminfo, channels):
        """Appends channel information to stream description"""
        xml_channels = streaminfo.desc().append_child("channels")
        for channel in channels:
            xml_channels.append_child("channel").append_child_value("label", channel)

    @staticmethod
    def _generate_primitive_sample(payload):
        """Combine payload's primitive fields into sample"""
        return (
            payload.get("diameter", -1.0),
            payload["confidence"],
            payload["timestamp"],
            payload["norm_pos"][0],
            payload["norm_pos"][1],
        )

    def construct_streaminfo(self):
        self.setup_channels()
        stream_info = lsl.StreamInfo(
            name="pupil_capture",
            type="Gaze",
            channel_count=len(self.channels),
            channel_format=lsl.cf_double64,
        )
        for chan in self.channels:
            chan.append_to_streaminfo(stream_info)

    def setup_channels(self):
        self.channels = [self.confidence_channel()]
        self.channels.extend(self.norm_pos_channels())
        self.channels.extend(self.gaze_point_3d_channels())
        self.channels.extend(self.eye_center_channels())
        self.channels.extend(self.gaze_normal_channels())
        self.channels.extend(self.diameter_2d_channels())
        self.channels.extend(self.diameter_3d_channels())

    def confidence_channel(self):
        return _Channel(
            query=extract_confidence,
            label="confidence",
            eye="both",
            metatype="Confidence",
            unit="normalized",
        )

    def norm_pos_channels(self):
        return [
            _Channel(
                query=make_extract_normpos(i),
                label="norm_pos_" + "xy"[i],
                eye="both",
                metatype="Screen" + "XY"[i],
                unit="normalized",
                coordinate_system="world",
            )
            for i in range(2)
        ]

    def gaze_point_3d_channels(self):
        return [
            _Channel(
                query=make_extract_gaze_point_3d(i),
                label="gaze_point_3d_" + "xyz"[i],
                eye="both",
                metatype="Direction" + "XYZ"[i],
                unit="mm",
                coordinate_system="world",
            )
            for i in range(3)
        ]

    def eye_center_channels(self):
        return [
            _Channel(
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

    def gaze_normal_channels(self):
        return [
            _Channel(
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

    def diameter_2d_channels(self):
        return [
            _Channel(
                query=make_extract_diameter_2d(eye),
                label="diameter{}_2d".format(eye),
                eye=("right", "left")[eye],
                metatype="Diameter",
                unit="pixels",
                coordinate_system="eye{}".format(eye),
            )
            for eye in range(2)
        ]

    def diameter_3d_channels(self):
        return [
            _Channel(
                query=make_extract_diameter_3d(eye),
                label="diameter{}_3d".format(eye),
                eye=("right", "left")[eye],
                metatype="Diameter",
                unit="mm",
                coordinate_system="eye{}".format(eye),
            )
            for eye in range(2)
        ]


class _Channel:
    def __init__(self, query, label, eye, metatype, unit, coordinate_system=None):
        self.label = label
        self.eye = eye
        self.metatype = metatype
        self.unit = unit
        self.coordinate_system = coordinate_system
        self.query = query

    def append_to(self, channels):
        chan = channels.append_child("channel")
        chan.append_child_value("label", self.label)
        chan.append_child_value("eye", self.eye)
        chan.append_child_value("type", self.metatype)
        chan.append_child_value("unit", self.unit)
        if self.coordinate_system:
            chan.append_child_value("coordinate_system", self.coordinate_system)


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
            return gaze["eye_centers_3d"][eye][dim]
        elif topic.endswith("3d.{}.".format(eye)):
            return gaze["eye_center_3d"][dim]
        else:
            return np.nan

    return extract_eye_center_3d


def make_extract_gaze_normal_3d(eye, dim):
    def extract_gaze_normal_3d(gaze):
        topic = gaze["topic"]
        if topic.endswith("3d.01."):
            return gaze["gaze_normals_3d"][eye][dim]
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
            if pupil["id"] == eye:
                return pupil["diameter_3d"]
        else:
            return np.nan

    return extract_diameter_3d
