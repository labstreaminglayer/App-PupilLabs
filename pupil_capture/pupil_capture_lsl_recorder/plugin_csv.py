import csv
import itertools
import logging
import os
import typing as T

import pylsl as lsl
from plugin import Plugin
from pyglui import ui
from version_utils import parse_version

from .recorder import StreamRecorder, _stream_label

VERSION = "1.0"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LSL_CSV_Recorder(Plugin):
    icon_chr = "LSL\nrec"
    icon_pos_delta = (0, -6)
    icon_size_delta = -15
    icon_line_height = 0.8

    # -- Plugin callbacks

    def __init__(self, g_pool, streams_should_record=None):
        super().__init__(g_pool)
        if g_pool.version < parse_version("3.4.59"):
            self.icon_chr = "RC"  # no icon custimization available yet
        self._is_recording = False
        self._streams = {}
        self._streams_should_record = streams_should_record or {}
        self._stream_recorders = []
        self._resolver = lsl.ContinuousResolver()

    def get_init_dict(self):
        return {"streams_should_record": self._streams_should_record}

    # -- Plugin callbacks

    def init_ui(self):
        """Initializes sidebar menu"""
        self.add_menu()
        self.menu.label = "CSV LSL Recorder"
        self.menu.append(
            ui.Info_Text(
                f"Version {VERSION} - "
                "Select and record LSL streams in Pupil Capture time."
            )
        )
        self.menu.append(
            ui.Info_Text(
                "This plugin uses the LSL framework to receive data from other LSL "
                "sources (outlets) and stores it in CSV format as part of the native "
                "Pupil Capture recordings."
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
            CSVStreamRecorder(stream, directory, self.g_pool.get_timestamp)
            for stream in self.streams_to_record()
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


class CSVStreamRecorder(StreamRecorder):
    def __init__(
        self,
        stream: lsl.StreamInfo,
        rec_dir: str,
        pupil_clock: T.Callable[[], float],
        timeout: float = 1.0,
    ) -> None:
        super().__init__(stream, rec_dir, pupil_clock, timeout)
        file_name = f"lsl_{stream.name()}_{stream.hostname()}_{stream.source_id()}.csv"
        file_path = os.path.join(rec_dir, file_name)
        self.file_handle = open(file_path, "w")
        self.csv_writer = csv.writer(self.file_handle)
        self._record_header()
        self.record_available_data()

    def close(self):
        super().close()
        self.file_handle.close()

    def _record_header(self):
        self.csv_writer.writerow(self._csv_header())

    def _record_chunk(self, timestamp_offset: float):
        chunk = self.inlet.pull_chunk()
        rows = [
            itertools.chain((ts + timestamp_offset,), datum)
            for datum, ts in zip(*chunk)
        ]
        self.csv_writer.writerows(rows)
        return len(rows)

    def _csv_header(self):
        yield "timestamp"
        labels = list(self._channel_labels())
        if not labels:
            labels = (f"channel_{i}" for i in range(self.info.channel_count()))
        yield from labels

    def _channel_labels(self):
        description = self.info.desc()
        channel = description.child("channels").first_child()
        while not channel.empty():
            yield channel.child_value("label")
            channel = channel.next_sibling()
