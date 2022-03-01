import logging
import time
import uuid

import pylsl as lsl

VERSION = "1.0"


logger = logging.getLogger(__name__)


class PupilInvisibleGazeRelay:
    def __init__(self, outlet_uuid=None):
        self._channels = pi_gaze_channels()
        self._time_offset = time.time() - lsl.local_clock()
        self._outlet_uuid = outlet_uuid or str(uuid.uuid4())
        self._outlet = pi_gaze_outlet(self._outlet_uuid, self._channels)

    def push_gaze_sample(self, gaze):
        try:
            sample = [chan.query(gaze) for chan in self._channels]
            timestamp = gaze.timestamp - self._time_offset
        except Exception as exc:
            logger.error(f"Error extracting gaze sample: {exc}")
            logger.debug(str(gaze))
            return
        # push_chunk might be more efficient but does not
        # allow to set explicit timstamps for all samples
        self._outlet.push_sample(sample, timestamp)


def pi_gaze_outlet(outlet_uuid, channels):
    stream_info = pi_streaminfo(outlet_uuid, channels)
    return lsl.StreamOutlet(stream_info)


def pi_streaminfo(outlet_uuid, channels):
    stream_info = lsl.StreamInfo(
        name="pupil_invisible",
        type="Gaze",
        channel_count=len(channels),
        channel_format=lsl.cf_double64,
        source_id=outlet_uuid,
    )
    stream_info.desc().append_child_value("pupil_invisible_lsl_relay_version", VERSION)
    xml_channels = stream_info.desc().append_child("channels")
    for chan in channels:
        chan.append_to(xml_channels)
    return stream_info


def pi_gaze_channels():
    channels = []

    # ScreenX, ScreenY: screen coordinates of the gaze cursor
    channels.extend(
        [
            GazeChannel(
                query=pi_extract_screen_query(i),
                label="xy"[i],
                eye="both",
                metatype="Screen" + "XY"[i],
                unit="pixels",
                coordinate_system="world",
            )
            for i in range(2)
        ]
    )

    # PupilInvisibleTimestamp: original Pupil Invisible UNIX timestamp
    channels.extend(
        [
            GazeChannel(
                query=pi_extract_timestamp_query(),
                label="pi_timestamp",
                eye="both",
                metatype="PupilInvisibleTimestamp",
                unit="seconds",
            )
        ]
    )

    return channels


def pi_extract_screen_query(dim):
    return lambda gaze: [gaze.x, gaze.y][dim]


def pi_extract_timestamp_query():
    return lambda gaze: gaze.timestamp


class GazeChannel:
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
