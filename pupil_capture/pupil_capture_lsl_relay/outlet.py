"""
(*)~----------------------------------------------------------------------------------
 Pupil LSL Relay
 Copyright (C) 2012 Pupil Labs

 Distributed under the terms of the GNU Lesser General Public License (LGPL v3.0).
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
"""
import abc
import logging
from typing import Optional, Sequence
from uuid import uuid4 as generate_uuid

import pylsl as lsl

from .channel import Channel
from .version import VERSION

logger = logging.getLogger(__name__)


class Outlet(abc.ABC):
    # concrete functionality to be implemented:

    @property
    @abc.abstractmethod
    def name(self) -> str:
        return NotImplementedError

    @property
    @abc.abstractmethod
    def event_key(self) -> str:
        return NotImplementedError

    @abc.abstractmethod
    def setup_channels(self) -> Sequence[Channel]:
        raise NotImplementedError

    # abstract functionality:

    _name_to_type_mapping = {}

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        cls._name_to_type_mapping[cls.type_name()] = cls

    @classmethod
    def type_name(cls) -> str:
        return cls.__name__

    @classmethod
    def available_type_names(cls) -> Sequence[str]:
        return tuple(cls._name_to_type_mapping.keys())

    @classmethod
    def setup(cls, outlet_type_name: str, uuid: Optional[str] = None):
        """Factory method that initializes subclassed outlets"""
        try:
            outlet_type = cls._name_to_type_mapping[outlet_type_name]
        except KeyError as cause:
            raise ValueError(f"Unknown Outlet type {outlet_type_name}") from cause
        return outlet_type(uuid)

    def __init__(self, uuid: str) -> None:
        self._uuid = uuid or str(generate_uuid())
        self.channels = self.setup_channels()
        stream_info = self.construct_streaminfo()
        self._wrapped_outlet = lsl.StreamOutlet(stream_info)

    def push_sample(self, sample):
        try:
            channel_data = self.extract_channel_data(sample)
        except Exception:
            logger.exception(f"Error extracting sample: {sample}")
            return
        # push_chunk might be more efficient but does not
        # allow to set explicit timstamps for all samples
        self._wrapped_outlet.push_sample(channel_data, sample["timestamp"])

    def extract_channel_data(self, sample):
        return [chan.query(sample) for chan in self.channels]

    def construct_streaminfo(self) -> lsl.StreamInfo:
        stream_info = lsl.StreamInfo(
            name=self.name,
            type=self.lsl_type,
            channel_count=len(self.channels),
            channel_format=lsl.cf_double64,
            source_id=self.uuid,
        )
        stream_info.desc().append_child_value("pupil_lsl_relay_version", VERSION)
        xml_channels = stream_info.desc().append_child("channels")
        for chan in self.channels:
            chan.append_to(xml_channels)
        logger.debug(f"Creating {self.name} outlet with stream info:\n{stream_info}")
        return stream_info

    @property
    def lsl_type(self) -> str:
        return "Gaze"

    @property
    def uuid(self) -> str:
        return self._uuid
