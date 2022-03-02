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
    fixation_dispersion_channel,
    fixation_duration_channel,
    fixation_id_channel,
    fixation_method_channel,
    norm_pos_channels,
)
from .outlet import Outlet


class SceneCameraFixations(Outlet):
    @property
    def name(self) -> str:
        return "pupil_capture_fixations"

    @property
    def event_key(self) -> str:
        return "fixations"

    @property
    def lsl_type(self) -> str:
        return "Fixations"

    def setup_channels(self):
        return (
            fixation_id_channel(),
            confidence_channel(),
            *norm_pos_channels(),
            fixation_dispersion_channel(),
            fixation_duration_channel(),
            fixation_method_channel(),
        )
