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

import zmq
import zmq_tools
from pyre import zhelper

from plugin import Plugin
from pyglui import ui

import pylsl as lsl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

NOTIFY_SUB_TOPIC = "notify"
PUPIL_SUB_TOPIC = "pupil"
GAZE_SUB_TOPIC = "gaze"

PRIMITIVE = "primitive"
MSGPACK = "msgpack"
DISABLED = "disabled"


class Pupil_LSL_Relay(Plugin):
    """Plugin to relay Pupil Capture data to LSL

    All stream outlets are of type _Pupil Capture_.

    Primitive data streams consist of 5 channels (lsl.cf_double64):
        - diameter (-1.0 for gaze streams)
        - confidence
        - timestamp
        - norm_pos.x
        - norm_pos.y

    Msgpack Representation streams consist of 1 channel containing the
    msgpack serialization of the datum.

    The plugin provides following outlets:

        relay_pupil:
            - Pupil Primitive Data
            - Pupil Msgpack Representation

        relay_gaze:
            - Gaze Primitive Data
            - Gaze Msgpack Representation

        relay_notifications:
            - Notification Msgpack Representation

    """

    icon_chr = "LR"

    def __init__(
        self,
        g_pool,
        relay_pupil=PRIMITIVE,
        relay_gaze=PRIMITIVE,
        relay_notifications=MSGPACK,
    ):
        """Summary

        Args:
            relay_pupil (str, optional): Pupil data relay option ("primitive" (default), "msgpack", "disabled")
            relay_gaze (str, optional): Gaze data relay option ("primitive" (default), "msgpack", "disabled")
            relay_notifications (str, optional): Notifications relay  option ("msgpack" (default), "disabled")
        """
        super().__init__(g_pool)
        self.relay_pupil = relay_pupil
        self.relay_gaze = relay_gaze
        self.relay_notifications = relay_notifications
        self.context = g_pool.zmq_ctx
        self.thread_pipe = zhelper.zthread_fork(self.context, self.thread_loop)

    def init_ui(self):
        """Initializes sidebar menu"""
        self.add_menu()
        self.menu.label = "Pupil LSL Relay"

        def make_setter(sub_topic, attribute_name):
            def set_value(value):
                setattr(self, attribute_name, value)
                self.thread_pipe.send_string(sub_topic, flags=zmq.SNDMORE)
                self.thread_pipe.send_string(value)

            return set_value

        self.menu.append(
            ui.Info_Text(
                "Pupil LSL Relay subscribes to the Pupil ZMQ Backbone and relays"
                " the incoming data using the lab streaming layer."
            )
        )
        self.menu.append(
            ui.Info_Text(
                "Primitive data streams contain diameter, confidence, timestamp,"
                " norm_pos.x, and norm_pos.y values. Msgpack data streams contain"
                " the msgpack representation of the complete datum."
            )
        )
        self.menu.append(
            ui.Selector(
                "relay_pupil",
                self,
                label="Relay pupil data",
                setter=make_setter(PUPIL_SUB_TOPIC, "relay_pupil"),
                selection=[DISABLED, PRIMITIVE, MSGPACK],
            )
        )
        self.menu.append(
            ui.Selector(
                "relay_gaze",
                self,
                label="Relay gaze data",
                setter=make_setter(GAZE_SUB_TOPIC, "relay_gaze"),
                selection=[DISABLED, PRIMITIVE, MSGPACK],
            )
        )
        self.menu.append(
            ui.Selector(
                "relay_notifications",
                self,
                label="Relay notifications",
                setter=make_setter(NOTIFY_SUB_TOPIC, "relay_notifications"),
                selection=[DISABLED, MSGPACK],
            )
        )

    def get_init_dict(self):
        """Store settings"""
        return {
            "relay_pupil": self.relay_pupil,
            "relay_gaze": self.relay_gaze,
            "relay_notifications": self.relay_notifications,
        }

    def deinit_ui(self):
        self.remove_menu()

    def cleanup(self):
        """gets called when the plugin get terminated.
           This happens either voluntarily or forced.
        """
        self.shutdown_thread_loop()

    def shutdown_thread_loop(self):
        if self.thread_pipe:
            self.thread_pipe.send_string("Exit")
            while self.thread_pipe:
                sleep(0.1)

    def thread_loop(self, context, pipe):
        """Background Relay Thread

        1. Connects to the ZMQ backbone
        2. Creates LSL outlets according to settings
        3. Subscibes to according topics
        4. Loop
        4.1. Relay data
        4.2. Handle un/subscription events
        4.3. Handle exit event
        5. Shutdown background thread
        """
        try:
            logger.debug("Connecting to %s..." % self.g_pool.ipc_sub_url)
            manager = RelayManager(pipe, context, self.g_pool.ipc_sub_url)

            manager.add_relay(PUPIL_SUB_TOPIC, self.relay_pupil)
            manager.add_relay(GAZE_SUB_TOPIC, self.relay_gaze)
            manager.add_relay(NOTIFY_SUB_TOPIC, self.relay_notifications)

            manager.spin()  # spins endlessly

            manager.close()

        except Exception as e:
            logger.error(
                "Error during relaying data to LSL. " + "Unloading the plugin..."
            )
            logger.debug("Error details: %s" % e)
            raise
        finally:
            logger.debug("Shutting down background thread...")
            self.thread_pipe = None
            self.alive = False


class RelayManager:
    def __init__(self, management_pipe, zmq_context, subscribtion_url):
        self.pipe = management_pipe
        self.ctx = zmq_context
        self.url = subscribtion_url

        self.poller = zmq.Poller()
        self.poller.register(self.pipe, zmq.POLLIN)

        self.relays = {}
        self.relay_by_socket = {}

    def add_relay(self, topic, initial_mode):
        subscriber = zmq_tools.Msg_Receiver(
            self.ctx, self.url, block_until_connected=False
        )
        relay = Relay(subscriber, topic, initial_mode)
        self.relays[topic] = relay
        self.relay_by_socket[relay.socket] = relay
        self.poller.register(relay.socket, zmq.POLLIN)

    def remove_relay(self, topic):
        relay = self.relays[topic]
        self.poller.unregister(relay.socket)
        del self.relay_by_socket[relay.socket]
        del self.relays[topic]

    def spin(self):
        while True:
            for socket, event in self.poller.poll():
                try:
                    self.relay_by_socket[socket].relay()
                except KeyError:
                    topic_or_cmd = self.pipe.recv_string()
                    if topic_or_cmd == "Exit":
                        return
                    else:
                        mode = self.pipe.recv_string()
                        self.relays[topic_or_cmd].mode = mode

    def close(self):
        # we need a copy of the keys since `remove_relay` modifies `relays`
        for topic in tuple(self.relays.keys()):
            self.remove_relay(topic)
        self.poller.unregister(self.pipe)


class Relay:
    def __init__(self, subscriber, topic, mode):
        self._mode = DISABLED
        self.subscriber = subscriber
        self.topic = topic
        self.mode = mode

    @property
    def socket(self):
        return self.subscriber.socket

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, new_mode):
        if self.mode == new_mode:
            return
        elif new_mode == DISABLED:
            self.subscriber.unsubscribe(self.topic)
            self.outlet = None
        elif new_mode == PRIMITIVE:
            self.subscriber.subscribe(self.topic)
            self.outlet = self._create_primitive_lsl_outlet()
        elif new_mode == MSGPACK:
            self.subscriber.subscribe(self.topic)
            self.outlet = self._create_msgpack_lsl_outlet()
        else:
            raise ValueError("Unknown mode `{}`".format(new_mode))
        self._mode = new_mode

    def relay(self):
        while self.subscriber.new_data:
            topic = self.subscriber.recv_topic()
            remaining_frames = self.subscriber.recv_remaining_frames()
            if self.mode == PRIMITIVE:
                payload = self.subscriber.deserialize_payload(*remaining_frames)
                self.outlet.push_sample(self._generate_primitive_sample(payload))
            elif self.mode == MSGPACK:
                payload = tuple(remaining_frames)[:1]
                self.outlet.push_sample(payload)
            else:
                raise AttributeError("Invalid mode `{}`".format(self.mode))

    @staticmethod
    def _append_acquisition_info(streaminfo):
        """Appends acquisition information to stream description"""
        acquisition = streaminfo.desc().append_child("acquisition")
        acquisition.append_child_value("manufacturer", "Pupil Labs")
        acquisition.append_child_value("source", "Pupil LSL Relay Plugin")

    def _create_primitive_lsl_outlet(self):
        """Create 5 channel primitive data outlet"""
        stream_info = lsl.StreamInfo(
            name="{}_primitive".format(self.topic),
            type="pupil_capture",
            channel_count=5,
            channel_format=lsl.cf_double64,
        )
        self._append_channel_info(
            stream_info,
            ("diameter", "confidence", "timestamp", "norm_pos_x", "norm_pos_y"),
        )
        self._append_acquisition_info(stream_info)
        return lsl.StreamOutlet(stream_info)

    def _create_msgpack_lsl_outlet(self):
        """Create 1 channel msgpack representation outlet"""
        stream_info = lsl.StreamInfo(
            name="{}_msgpack".format(self.topic),
            type="pupil_capture",
            channel_count=1,
            channel_format=lsl.cf_int8,
        )
        self._append_channel_info(stream_info, ("Msgpack Representation",))
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
