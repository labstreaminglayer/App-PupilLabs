"""
(*)~----------------------------------------------------------------------------------
 Pupil LSL Relay
 Copyright (C) 2012 Pupil Labs

 Distributed under the terms of the GNU Lesser General Public License (LGPL v3.0).
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
"""

import logging
from typing import Iterable, Tuple

import pylsl as lsl
from plugin import Plugin
from pyglui import ui
from version_utils import parse_version

from .outlet import Outlet
from .version import VERSION

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Pupil_LSL_Relay(Plugin):
    """Plugin to relay Pupil Capture data to LSL

    Initializes one outlet for every available type, e.g. scene camera gaze.
    Each outlet is responsible for extracting its required information from the provided
    samples. The latter are based on the outlet's `event_key`.
    """

    icon_chr = "LSL\nrelay"
    icon_pos_delta = (0, -7)
    icon_size_delta = -15
    icon_line_height = 0.8
    order = 0.89
    """plugin order

    highest possible order before recorder - ensures that all data-generating plugins
    run first
    """

    def __init__(
        self,
        g_pool,
        previous_outlets: Iterable[Tuple[str, str]] = (),
        # kept for backwards compatibility with with previous plugin version's session
        # settings (`# type: ignore` disables code checker warnings):
        outlet_uuid=...,  # type: ignore
    ):
        super().__init__(g_pool)
        if g_pool.version < parse_version("3.4.59"):
            self.icon_chr = "RL"  # no icon custimization available yet
        self.adjust_pupil_to_lsl_time()
        self.setup_outlets(previous_outlets)

    def adjust_pupil_to_lsl_time(self):
        debug_ts_before = self.g_pool.get_timestamp()
        time_dif = self.g_pool.get_now() - lsl.local_clock()
        self.g_pool.timebase.value = time_dif
        debug_ts_after = self.g_pool.get_timestamp()
        debug_ts_lsl = lsl.local_clock()
        logger.info("Synchronized time epoch to LSL clock")
        logger.debug(f"Time before synchronization: {debug_ts_before}")
        logger.debug(f"Time after synchronization: {debug_ts_after}")
        logger.debug(f"LabStreamingLayer time: {debug_ts_lsl}")

    def setup_outlets(self, previous_outlets: Iterable[Tuple[str, str]]):
        """Initialize all available outlets and restoring previous source ids

        Takes care of not initializing outlet types that are no longer available.
        """
        outlet_config = {name: None for name in Outlet.available_type_names()}
        for name, uuid in previous_outlets:
            if name in outlet_config:
                outlet_config[name] = uuid
            else:
                logger.warning(f"Previous outlet type `{name}` not available!")
        self._outlets: Iterable[Outlet] = [
            Outlet.setup(name, uuid) for name, uuid in outlet_config.items()
        ]

    def recent_events(self, events):
        for outlet in self._outlets:
            for sample in events.get(outlet.event_key, ()):
                outlet.push_sample(sample)

    def init_ui(self):
        self.add_menu()
        self.menu.label = f"Pupil LSL Relay"
        self.menu.append(ui.Info_Text(f"Version {VERSION}"))
        self.menu.append(ui.Info_Text("Relays various Pupil Core data sources to LSL"))
        self.menu.append(
            ui.Info_Text(
                "Gaze data format follows: "
                "https://github.com/sccn/xdf/wiki/Gaze-Meta-Data"
            )
        )
        self.menu.append(ui.Info_Text("Available outlets:"))
        for outlet in self._outlets:
            self.menu.append(ui.Info_Text(f"- {outlet.name} ({outlet.lsl_type})"))

    def deinit_ui(self):
        self.remove_menu()

    def get_init_dict(self):
        return {"previous_outlets": [(o.type_name(), o.uuid) for o in self._outlets]}

    def cleanup(self):
        del self._outlets[:]
        self._outlets = None
