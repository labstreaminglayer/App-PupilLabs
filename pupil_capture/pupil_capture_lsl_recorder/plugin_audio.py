"""LSL Audio Recorder

Record incoming LSL audio streams as part of the native Pupil Capture recordings.

File format: mp4 container with aac audio; Pupil Player compatible format

Changes
^^^^^^^

- 1.0: initial version
"""

import logging
import os
import traceback
import typing as T
import warnings

import av
import numpy as np
import pylsl as lsl
from av_writer import _AudioPacketIterator
from plugin import Plugin
from pyglui import ui
from version_utils import parse_version

from .recorder import StreamRecorder, _stream_label

VERSION = "1.0"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LSL_Audio_Recorder(Plugin):
    icon_chr = chr(0xE029)
    icon_font = "pupil_icons"

    # -- Plugin callbacks

    def __init__(self, g_pool, streams_should_record=None):
        super().__init__(g_pool)
        if g_pool.version < parse_version("3.4.59"):
            self.icon_chr = "RC"  # no icon custimization available yet
        self._is_recording = False
        self._streams = {}
        self._streams_should_record = streams_should_record or {}
        self._stream_recorders = []
        self._resolver = lsl.ContinuousResolver(prop="type", value="Audio")

    def get_init_dict(self):
        return {"streams_should_record": self._streams_should_record}

    # -- Plugin callbacks

    def init_ui(self):
        """Initializes sidebar menu"""
        self.add_menu()
        self.menu.label = "LSL Audio Recorder"
        self.menu.append(
            ui.Info_Text(
                f"Version {VERSION} - "
                "Select and record LSL audio streams in Pupil Capture time."
            )
        )
        self.menu.append(
            ui.Info_Text(
                "This plugin uses the LSL framework to receive audio from another LSL "
                "source (outlet) and stores it as a mp4 audio file with timestamps as "
                "part of the native Pupil Capture recording. Pupil Player is able to "
                "playback the audio in sync with the remaining recording."
            )
        )
        self._streams_menu = ui.Growing_Menu("Streams to record")
        self.menu.append(self._streams_menu)

    def deinit_ui(self):
        self.remove_menu()
        del self._streams_menu[:]
        self._streams_menu = None

    def on_notify(self, notification):
        if notification["subject"] == "recording.started":
            self.start_recording(notification["rec_path"])
        elif notification["subject"] == "recording.stopped":
            self.stop_recording()

    def recent_events(self, events):
        if self._stream_recorders:
            for recorder in self._stream_recorders:
                recorder.record_available_data()
        else:
            self.resolve_lsl_streams()

    # -- Core logic

    def start_recording(self, directory):
        if self._is_recording:
            return
        self._set_recording_state(True)
        self._stream_recorders = [
            AudioStreamRecorder(stream, directory, self.g_pool.get_timestamp)
            for stream in list(self.streams_to_record())[:1]  # TODO: allow selection
        ]

    def stop_recording(self):
        if not self._is_recording:
            return
        for recorder in self._stream_recorders:
            recorder.close()
        del self._stream_recorders[:]
        self._set_recording_state(False)

    def streams_to_record(self):
        if not self._is_recording:
            return
        yield from (
            stream
            for stream in self._streams.values()
            if self._streams_should_record[_stream_label(stream)]
        )

    def resolve_lsl_streams(self):
        streams = {stream.source_id(): stream for stream in self._resolver.results()}
        stream_ids_new = set(streams) - set(self._streams)
        stream_ids_removed = set(self._streams) - set(streams)
        self._streams = streams

        potentially_new_entries = {
            _stream_label(streams[stream_id]) for stream_id in stream_ids_new
        }
        new_entries = potentially_new_entries - self._streams_should_record.keys()
        self._streams_should_record.update({entry: True for entry in new_entries})

        if stream_ids_new or stream_ids_removed:
            stream_labels = [_stream_label(stream) for stream in self._streams.values()]
            del self._streams_menu[:]
            for stream_source_id, label in zip(self._streams, stream_labels):
                self._add_stream(stream_source_id, label)

    def _set_recording_state(self, state):
        self._is_recording = state
        for button in self._streams_menu:
            button.read_only = state

    def _add_stream(self, stream_source_id, label):
        self._streams_menu.append(ui.Switch(label, self._streams_should_record))


class AudioStreamRecorder(StreamRecorder):
    def __init__(
        self,
        stream: lsl.StreamInfo,
        rec_dir: str,
        pupil_clock: T.Callable[[], float],
        timeout: float = 1.0,
    ) -> None:
        super().__init__(stream, rec_dir, pupil_clock, timeout)
        file_path_audio = os.path.join(rec_dir, "audio.mp4")
        self.file_path_ts = os.path.join(rec_dir, "audio_timestamps.npy")
        self.start_time = None
        self.timestamps = []
        self.container = av.open(file_path_audio, "w")
        self._counter_frames_dopped = 0

        inlet_info = self.inlet.info()
        self.sample_rate = round(inlet_info.nominal_srate())
        channel_format_lsl = inlet_info.channel_format()
        self.channel_format_dtype = lsl.pylsl.fmt2string[channel_format_lsl]
        if self.channel_format_dtype == "int8":
            self.channel_format_dtype = "uint8"

        self.channel_format_audio = {
            lsl.cf_int8: "u8p",
            lsl.cf_int16: "s16p",
            lsl.cf_int32: "s32p",
            lsl.cf_float32: "fltp",
            lsl.cf_double64: "dblp",
        }[channel_format_lsl]

        self.audio_stream = self.container.add_stream("aac", rate=self.sample_rate)
        self.audio_stream.codec_context.layout = "stereo"
        self.resampler = av.AudioResampler(
            format=self.audio_stream.codec_context.format,
            layout=self.audio_stream.codec_context.layout,
            rate=self.sample_rate,
        )

        self.record_available_data()

    def close(self):
        super().close()
        try:
            for packet in self.audio_stream.encode(None):
                self.container.mux(packet)
        except ValueError as err:
            warnings.warn(UserWarning(f"Dropped at least one frame due to: {err}"))
            self._counter_frames_dopped += 1

        self.container.close()
        np.save(self.file_path_ts, self.timestamps)
        logger.info(
            f"{len(self.timestamps)} audio frames recorded. "
            f"{self._counter_frames_dopped} audio frames dropped."
        )

    def _record_chunk(self, timestamp_offset: float):
        samples, timestamps = self.inlet.pull_chunk()
        timestamps = np.array(timestamps) + timestamp_offset

        if timestamps.shape[0] > 0 and self.start_time is None:
            self.start_time = timestamps[0]
            logger.info(
                f"Audio recording started: ({self.channel_format_audio} @ "
                f"{self.sample_rate} Hz)"
            )

        if samples:
            samples = np.array(
                samples, dtype=self.channel_format_dtype
            )  # shape: m_samples x n_channels
            samples = samples.T  # av.AudioFrame expects n_channels x m_samples
            if samples.shape[0] < 2:
                samples = samples[[0, 0]]  # convert mono to stereo by copying channel
            elif samples.shape[0] > 2:
                samples = samples[:2]  # only record the first two channels

            frame = AudioFrame_from_ndarray(
                np.ascontiguousarray(samples),
                format=self.channel_format_audio,
                layout="stereo",
            )
            frame.sample_rate = self.sample_rate
            time_to_first_sample = timestamps[0] - self.start_time
            frame.pts = int(time_to_first_sample * self.sample_rate)
            frame.time_base = self.sample_rate
            try:
                resampled = self.resampler.resample(frame)
            except (ValueError, av.AVError, ValueError) as err:
                warnings.warn(
                    UserWarning(
                        f"Dropped at least one frame ({frame}) due to resampling "
                        f"error: {err}"
                    )
                )
                logger.debug(traceback.format_exc())
                self._counter_frames_dopped += 1
                return
            try:
                for packet in self.audio_stream.encode(resampled):
                    self.container.mux(packet)
                    self.timestamps.append(timestamps[0])
            except (ValueError, av.AVError, ValueError) as err:
                warnings.warn(
                    UserWarning(
                        f"Dropped at least one frame ({resampled}) due to encoding "
                        f"error: {err}"
                    )
                )
                logger.debug(traceback.format_exc())
                self._counter_frames_dopped += 1
                return


def AudioFrame_from_ndarray(array, format="s16", layout="stereo"):
    """
    Source: https://github.com/PyAV-Org/PyAV/blob/main/av/audio/frame.pyx#L107-L132
    """
    # map avcodec type to numpy type
    try:
        dtype = np.dtype(_AudioPacketIterator._format_dtypes[format])
    except KeyError:
        raise ValueError(
            "Conversion from numpy array with format `%s` is not yet supported" % format
        )

    # check input format
    nb_channels = len(av.AudioLayout(layout).channels)
    check_ndarray(array, dtype, 2)
    if av.AudioFormat(format).is_planar:
        check_ndarray_shape(array, array.shape[0] == nb_channels)
        samples = array.shape[1]
    else:
        samples = array.shape[1] // nb_channels

    frame = av.AudioFrame(format=format, layout=layout, samples=samples)
    for i, plane in enumerate(frame.planes):
        plane.update(array[i, :])
    return frame


def check_ndarray(array, dtype, ndim):
    """
    Source: https://github.com/PyAV-Org/PyAV/blob/main/av/utils.pyx#L65-L72
    """
    if array.dtype != dtype:
        raise ValueError(
            f"Expected numpy array with dtype `{dtype}` but got `{array.dtype}`"
        )
    if array.ndim != ndim:
        raise ValueError(
            f"Expected numpy array with ndim `{ndim}` but got `{array.ndim}`"
        )


def check_ndarray_shape(array, ok: bool):
    """
    Source: https://github.com/PyAV-Org/PyAV/blob/main/av/utils.pyx#L75-L80
    """
    if not ok:
        raise ValueError(f"Unexpected numpy array shape `{array.shape}`")
