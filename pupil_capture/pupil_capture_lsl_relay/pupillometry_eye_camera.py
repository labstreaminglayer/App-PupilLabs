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
    norm_pos_channels,
)
from .outlet import Outlet


class EyeCameraPupillometry(Outlet):
    @property
    def name(self) -> str:
        return "pupil_capture_pupillometry_only"

    @property
    def event_key(self) -> str:
        return "pupil"

    def setup_channels(self):
        return (
            confidence_channel(),
            *norm_pos_channels(coordinate_system="eye"),
            *diameter_2d_channels(),
            *diameter_3d_channels(),
        )
