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
import uuid

import numpy as np
import pylsl as lsl

from plugin import Plugin
from pyglui import ui


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Pupil_LSL_Relay(Plugin):
    """Plugin to relay Pupil Capture data to LSL"""

    icon_chr = "LR"

    def __init__(self, g_pool, outlet_uuid=None):
        super().__init__(g_pool)
        debug_ts_before = g_pool.get_timestamp()
        time_dif = g_pool.get_now() - lsl.local_clock()
        g_pool.timebase.value = time_dif
        debug_ts_after = g_pool.get_timestamp()
        debug_ts_lsl = lsl.local_clock()
        logger.info("Synchronized time epoch to LSL clock")
        logger.debug("Time before synchronization: {}".format(debug_ts_before))
        logger.debug("Time after synchronization: {}".format(debug_ts_after))
        logger.debug("LabStreamingLayer time: {}".format(debug_ts_lsl))

        self.outlet_uuid = outlet_uuid or str(uuid.uuid4())
        self.outlet = self.construct_outlet()

    def recent_events(self, events):
        if not self.outlet.have_consumers():
            return
        for gaze in events.get("gaze", ()):
            self.push_gaze_sample(gaze)

    def push_gaze_sample(self, gaze):
        try:
            sample = self.extract_gaze_sample(gaze)
        except Exception as exc:
            logger.error("Error extracting gaze sample: {}".format(exc))
            logger.debug(str(gaze))
            return
        # push_chunk might be more efficient but does not
        # allow to set explicit timstamps for all samples
        self.outlet.push_sample(sample, gaze["timestamp"])

    def extract_gaze_sample(self, gaze):
        return [chan.query(gaze) for chan in self.channels]

    def init_ui(self):
        """Initializes sidebar menu"""
        self.add_menu()
        self.menu.label = "Pupil LSL Relay"
        self.menu.append(ui.Info_Text("LSL outlet name: `pupil_capture`"))
        self.menu.append(
            ui.Info_Text(
                "LSL outlet format: https://github.com/sccn/xdf/wiki/Gaze-Meta-Data"
            )
        )

    def deinit_ui(self):
        self.remove_menu()

    def get_init_dict(self):
        return {"outlet_uuid": self.outlet_uuid}

    def cleanup(self):
        """gets called when the plugin get terminated.
           This happens either voluntarily or forced.
        """
        self.outlet = None

    def construct_outlet(self):
        self.setup_channels()
        stream_info = self.construct_streaminfo()
        return lsl.StreamOutlet(stream_info)

    def construct_streaminfo(self):
        self.setup_channels()
        stream_info = lsl.StreamInfo(
            name="pupil_capture",
            type="Gaze",
            channel_count=len(self.channels),
            channel_format=lsl.cf_double64,
            source_id=self.outlet_uuid,
        )
        xml_channels = stream_info.desc().append_child("channels")
        for chan in self.channels:
            chan.append_to(xml_channels)
        return stream_info

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
