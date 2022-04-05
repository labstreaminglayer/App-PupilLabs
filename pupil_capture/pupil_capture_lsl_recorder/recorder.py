import abc
import logging
import typing as T

import pylsl as lsl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _stream_label(stream):
    return f"{stream.name()} ({stream.hostname()})"


class StreamRecorder(abc.ABC):
    def __init__(
        self,
        stream: lsl.StreamInfo,
        rec_dir: str,
        pupil_clock: T.Callable[[], float],
        timeout: float = 1.0,
    ) -> None:
        self.rec_dir = rec_dir
        self.inlet = lsl.StreamInlet(stream)
        self.info = self.inlet.info(timeout=timeout)
        self.pupil_clock = pupil_clock
        self.inlet.time_correction(timeout=timeout)
        self.inlet.open_stream(timeout=timeout)

    def record_available_data(self):
        try:
            pupil_lsl_offset = self.pupil_clock() - lsl.local_clock()
            pupil_lsl_offset += self.inlet.time_correction()
            while self._record_chunk(pupil_lsl_offset):
                pass  # loop breaks as soon as available data has been processed
        except lsl.LostError:
            logger.warning(f"Lost connection to LSL stream: {_stream_label(self.info)}")

    def close(self):
        self.record_available_data()
        self.inlet.close_stream()

    @abc.abstractmethod
    def _record_chunk(self, timestamp_offset) -> int:
        """:returns: number of processed samples"""
        raise NotImplementedError()
