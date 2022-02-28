"""
(*)~----------------------------------------------------------------------------------
 Pupil LSL Relay
 Copyright (C) 2012 Pupil Labs

 Distributed under the terms of the GNU Lesser General Public License (LGPL v3.0).
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
"""
from .channel import (
    confidence_channel,
    diameter_2d_channels,
    diameter_3d_channels,
    eye_center_channels,
    gaze_normal_channels,
    gaze_point_3d_channels,
    norm_pos_channels,
)
from .outlet import Outlet


class SceneCameraGaze(Outlet):
    @property
    def name(self) -> str:
        return "pupil_capture"

    @property
    def event_key(self) -> str:
        return "gaze"

    def setup_channels(self):
        return (
            confidence_channel(),
            *norm_pos_channels(),
            *gaze_point_3d_channels(),
            *eye_center_channels(),
            *gaze_normal_channels(),
            *diameter_2d_channels(),
            *diameter_3d_channels(),
        )
