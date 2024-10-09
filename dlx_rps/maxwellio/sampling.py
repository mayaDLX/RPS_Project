# -*- coding: utf-8 -*-
# @title      MaxwellIO sampling
# @file       sampling.py
# @author     Atsuhiro Nabeta, Romain Beaubois
# @copyright
# SPDX-FileCopyrightText: ©2023 Atsuhiro Nabeta <atsuhiro.nabeta.lab@gmail.com>
# SPDX-FileCopyrightText: ©2024 Romain Beaubois <beaubois@iis.u-tokyo.ac.jp>
# SPDX-License-Identifier: MIT
#
# @brief
# Functions to control streams of MaxOne through the API
# * spike stream
# * raw stream
#
# @details
# > **01 Jan 2023** : file creation (AN)
# > **01 Jul 2024** : add file header (RB)
# > **03 Jul 2024** : add generic versioning for spike stream (RB)
# > **03 Jul 2024** : patch spike stream for newer versions (RB)
# > **09 Jul 2024** : fix channel only deserialization (RB)

import random
from abc import ABC
from struct import Struct
from types import TracebackType
from typing import (
    List,
    Optional,
    Protocol,
    Tuple,
    Type,
    final,
    runtime_checkable,
)

import maxlab
import numpy as np
from numpy.typing import NDArray
from zmq import (
    Context,
    Socket,
    SocketOption,
    SocketType,
)

SAMPLING_FREQUENCY = 20000
"""Sampling frequency."""

FILTERED_DATA_STREAM_PORT = 7205
"""The port number for the filtered data stream on the MaxWell server."""

RAW_DATA_STREAM_PORT = 7204
"""The port number for the raw data stream on the MaxWell server."""

MAX_N_SAMPLING_CHANNELS = 1024
"""The maximum number of sampling channels."""

_N_MAGIC_SAMPLING_CHANNELS = 3
"""The magic number for interaction with stimulation contained in the array
of received amplitudes.
"""

_MAX_N_FULL_SAMPLING_CHANNELS = (
    MAX_N_SAMPLING_CHANNELS + _N_MAGIC_SAMPLING_CHANNELS
)
"""The maximum number of sampling channels including system used channels."""

_BUFFERING_TIME = 10
"""The time (sec) that buffering can be done."""

_BUFFER_SIZE = (
    _BUFFERING_TIME * SAMPLING_FREQUENCY * _MAX_N_FULL_SAMPLING_CHANNELS
)
"""The size of the buffer."""

_FRAME_NUMBER_STRUCT = Struct("<Q")
"""The struct for the frame number (int)."""

_AMPLITUDE_STRUCT = Struct("<f")
"""The struct for the raw data (float)."""

"""New spike event structure for version > 24.1"""
_NEW_ENC_BYTE_ORDER = "<"  # little endian
_NEW_ENC_FRAME_NO = "Q"  # unsigned long -> 8 bytes -> Ubuntu 20.04 / C++20
_NEW_ENC_AMP = "f"  # float -> 4 bytes -> Ubuntu 20.04 / C++20
_NEW_ENC_CHANNEL = "H"  # uint16_t -> 2 bytes -> always
_NEW_ENC_WELL_ID = "B"  # unsigned char -> 1 byte -> always
_NEW_ENC_PAD = "1B"  # memory alignment whatever issue

_NEW_SPIKE_EVENT_STRUCT = Struct(
    _NEW_ENC_BYTE_ORDER
    + _NEW_ENC_FRAME_NO
    + _NEW_ENC_AMP
    + _NEW_ENC_CHANNEL
    + _NEW_ENC_WELL_ID
    + _NEW_ENC_PAD
)

"""Old spike event structure for version < 24.1"""
_OLD_ENC_BYTE_ORDER = "<"  # little endian
_OLD_ENC_FRAME_NO = "Q"  # unsigned long -> 8 bytes -> Ubuntu 20.04 / C++20
_OLD_ENC_AMP = "f"  # float -> 4 bytes -> Ubuntu 20.04 / C++20
_OLD_ENC_CHANNEL = "i"  # uint16_t -> 2 bytes -> always
_OLD_ENC_WELL_ID = "B"  # unsigned char -> 1 byte -> always
_OLD_ENC_PAD = "7B"  # memory alignment whatever issue
_OLD_SPIKE_EVENT_STRUCT = Struct(
    _OLD_ENC_BYTE_ORDER
    + _OLD_ENC_PAD
    + _OLD_ENC_WELL_ID
    + _OLD_ENC_FRAME_NO
    + _OLD_ENC_CHANNEL
    + _OLD_ENC_AMP
)

try:
    # Version 24.1
    if maxlab.__git_hash__ == "45b31664d":
        _SPIKE_EVENT_STRUCT = _NEW_SPIKE_EVENT_STRUCT
    # Later version than 24.1
    else:
        _SPIKE_EVENT_STRUCT = _OLD_SPIKE_EVENT_STRUCT
except AttributeError:
    # Older version (22.1/22.2)
    _SPIKE_EVENT_STRUCT = _OLD_SPIKE_EVENT_STRUCT
"""
By Silvia's email:
    ...
    How that structure is laid out in memory, depends on the platform.
    Most of the time these four fields will like that be laid in memory
    like that:
    So when you read in the first 7 bytes,
    they have no meaning and they are there because of memory alignment
    issues. The 8th byte specifies the well-id, which is always 0 for
    MaxOne.
"""
"""
RB:
    ...
    Spike event struct changed with newer version so as orders and data coding
    changed in the process. There is now a 1 byte padding for whatever
    memory alignment issue
"""


@final
class SpikeEvent:
    """A class for representing a spike event."""

    def __init__(
        self,
        well_id: int,
        frame_number: int,
        channel: int,
        amplitude: float,
    ) -> None:
        """Initialize a new instance.

        Parameters
        ----------
        well_id : int
            The ID of the well where this event occurred.
        frame_number : int
            The number of the frame in which this spike was detected.
        channel : int
            The channel on which this spike was detected.
        amplitude : float
            The last negative amplitude when this spike was detected.
        """

        self.well_id = well_id
        self.frame_number = frame_number
        self.channel = channel
        self.amplitude = amplitude

    if _SPIKE_EVENT_STRUCT == _NEW_SPIKE_EVENT_STRUCT:

        @classmethod
        def _deserialize(
            cls,
            buffer: bytes,
        ) -> List["SpikeEvent"]:
            """Deserialize the specified bytes into the list of spike events.

            Parameters
            ----------
            buffer : bytes
                Bytes.

            Returns
            -------
            List[SpikeEvent]
                The list of deserialized spike events from the bytes.
            """

            # Set the class variable on the local one for performance.
            struct = _SPIKE_EVENT_STRUCT

            events: List[SpikeEvent] = []
            for i in range(0, len(buffer), struct.size):
                (
                    frame_no,
                    amplitude,
                    channel,
                    well_id,
                    *_,
                ) = struct.unpack_from(buffer, i)
                event = SpikeEvent(well_id, frame_no, channel, amplitude)
                events.append(event)

            return events

        @classmethod
        def _deserialize_channels(
            cls,
            buffer: bytes,
        ) -> List[int]:
            """Deserialize only the channel number from the specified bytes.

            Parameters
            ----------
            buffer : bytes
                Bytes

            Returns
            -------
            List[int]
                The list of deserialized channels from the bytes.
            """

            struct = _SPIKE_EVENT_STRUCT

            events: List[int] = []
            for i in range(0, len(buffer), struct.size):
                (
                    _,
                    _,
                    channel,
                    _,
                    *_,
                ) = struct.unpack_from(buffer, i)
                events.append(channel)

            return events

    else:

        @classmethod
        def _deserialize(
            cls,
            buffer: bytes,
        ) -> List["SpikeEvent"]:
            """Deserialize the specified bytes into the list of spike events.

            Parameters
            ----------
            buffer : bytes
                Bytes.

            Returns
            -------
            List[SpikeEvent]
                The list of deserialized spike events from the bytes.
            """

            # Set the class variable on the local one for performance.
            struct = _SPIKE_EVENT_STRUCT

            events: List[SpikeEvent] = []
            for i in range(0, len(buffer), struct.size):
                (
                    *_,
                    well_id,
                    frame_no,
                    channel,
                    amplitude,
                ) = struct.unpack_from(buffer, i)
                event = SpikeEvent(well_id, frame_no, channel, amplitude)
                events.append(event)

            return events

        @classmethod
        def _deserialize_channels(
            cls,
            buffer: bytes,
        ) -> List[int]:
            """Deserialize only the channel number from the specified bytes.

            Parameters
            ----------
            buffer : bytes
                Bytes

            Returns
            -------
            List[int]
                The list of deserialized channels from the bytes.
            """

            struct = _SPIKE_EVENT_STRUCT

            events: List[int] = []
            for i in range(0, len(buffer), struct.size):
                (
                    *_,
                    channel,
                    _,
                ) = struct.unpack_from(buffer, i)
                events.append(channel)

            return events


@final
class MaxWellStream:
    """A class for receiving sample and spike data via MaxWell's ZeroMQ."""

    def __init__(
        self,
        hostname: str = "localhost",
        timeout: int = 100,
        is_filtered_data_stream_used: bool = False,
    ) -> None:
        """Initialize a new instance.
        Initially, the instance is not yet connected to the MaxWell server.

        Parameters
        ----------
        hostname : str
            The hostname for the MaxWell server.
        timeout : int
            The timeout (ms) for receive operation on the socket.
        is_filtered_data_stream_used : bool
            True if connect to the filtered stream; otherwise, False.
        """

        self._hostname = hostname

        self._context = Context.instance()

        self._subscriber: Socket = self._context.socket(SocketType.SUB)
        self._subscriber.setsockopt(SocketOption.RCVHWM, 0)
        self._subscriber.setsockopt(SocketOption.RCVBUF, _BUFFER_SIZE)
        self._subscriber.setsockopt_string(SocketOption.SUBSCRIBE, "")
        self._subscriber.setsockopt(SocketOption.RCVTIMEO, timeout)

        self._is_filtered_data_stream_used = is_filtered_data_stream_used

    def __enter__(self) -> "MaxWellStream":
        """Call self "connect()" and return self when using "with" syntax.

        Returns
        -------
        SampleSource
            Self.
        """

        self.connect()
        return self

    def __exit__(self, *args) -> None:
        """Call self "disconnect()" when using "with" syntax."""

        self.disconnect()

    def connect(self) -> None:
        """Connect to the MaxWell server.
        This method blocks the current thread until it receives
        a synchronization message after connecting to the MaxWell server.
        """

        port: int
        if self._is_filtered_data_stream_used:
            port = FILTERED_DATA_STREAM_PORT
        else:
            port = RAW_DATA_STREAM_PORT

        address = f"tcp://{self._hostname}:{port}"
        self._subscriber.connect(address)

        # sync with the RCVMore mode stream
        while True:
            zmq_frame = self._subscriber.recv(copy=False)

            if not zmq_frame.more:
                break

    def disconnect(self) -> None:
        """Disconnect from the MaxWell server."""

        self._subscriber.close()

    def receive_frame_number(self) -> Tuple[int, bool]:
        """Receive the number of the current frame.
        This method blocks the current thread until it receives the frame data.

        Returns
        -------
        frame_number : int
            The number of the current frame.
        more : bool
            True if there are more message parts to receive; otherwise, False.
        """

        # Set the class variable on the local one for performance.
        struct = _FRAME_NUMBER_STRUCT

        zmq_frame = self._subscriber.recv(copy=False)
        number = struct.unpack(zmq_frame.bytes)[0]
        return (number, zmq_frame.more)

    def receive_amplitudes(self) -> Tuple[List[float], bool]:
        """Receive amplitudes for the current frame.
        This method can be called if receive_frame_number() results in
        more=True.

        Returns
        -------
        data : List[float]
            Amplitudes for the current frame.
        more : bool
            True if there are more message parts to receive; otherwise, False.
        """

        # Set the class variable on the local one for performance.
        struct = _AMPLITUDE_STRUCT

        zmq_frame = self._subscriber.recv(copy=False)
        data = [i[0] for i in struct.iter_unpack(zmq_frame.bytes)]
        return (data, zmq_frame.more)

    def receive_spike_events(self) -> List[SpikeEvent]:
        """Receive detected spike events.
        This method can be called if receive_amplitudes() results in more=True.

        Returns
        -------
        List[SpikeEvent]
            The list of detected spike events.
        """

        zmq_frame = self._subscriber.recv(copy=False)
        events = SpikeEvent._deserialize(zmq_frame.bytes)
        return events

    def receive_spike_channels(self) -> List[int]:
        """Retrieve a list of channels where spikes are detected.
        This method can be called if receive_amplitudes() results in more=True.

        Returns
        -------
        List[int]
            The list of channels where spikes are detected.
        """

        zmq_frame = self._subscriber.recv(copy=False)
        channels = SpikeEvent._deserialize_channels(zmq_frame.bytes)
        return channels


@runtime_checkable
class SpikeStream(Protocol):
    def connect(self) -> None:
        """Connect to a server producing spike events."""
        ...

    def disconnect(self) -> None:
        """Disconnect from the server producing spike events."""
        ...

    def receive_spike_channels(self) -> List[int]: ...


class SpikeStreamABC(SpikeStream, ABC):
    def __enter__(self) -> "SpikeStream":
        """Call self `connect()` and return self.

        Returns
        -------
        SpikeDetector
            Self.
        """

        self.connect()
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        exception_traceback: Optional[TracebackType],
    ) -> bool:
        """Call self `disconnect()`."""

        self.disconnect()
        return False


class DebugSpikeStream(SpikeStreamABC):
    """A class implementing `SpikeStream` for debugging."""

    def __init__(self) -> None:
        """Initialize a new instance."""

        super().__init__()

        self.frequency = 5
        self.n_concurrent_detections = 5
        self.n_channels = MAX_N_SAMPLING_CHANNELS
        self._next_frame = 0

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def receive_spike_channels(self) -> List[int]:
        # To improve the loop performance.
        frequency = self.frequency
        n_concurrent_detections = self.n_concurrent_detections
        last_channel_index = self.n_channels - 1

        detected = random.randint(1, frequency) == 1
        if detected:
            n_detections = random.randint(1, n_concurrent_detections)
            channels: List[int] = []
            for _ in range(n_detections):
                channel = random.randint(0, last_channel_index)
                channels.append(channel)
            return channels
        else:
            return []


class MaxWellSpikeStream(SpikeStreamABC):
    """A class implementing `SpikeStream` to sample data via
    `MaxWellStream`.
    """

    def __init__(
        self,
        hostname: str = "localhost",
    ) -> None:
        """Instantiate a new instance.

        Parameters
        ----------
        hostname : str
            The hostname for the MaxWell server.
        """

        super().__init__()

        self._hostname = hostname

        self._stream: Optional[MaxWellStream] = None

    def connect(self) -> None:
        if self._stream is not None:
            return

        self._stream = MaxWellStream(self._hostname)
        self._stream.connect()

    def disconnect(self) -> None:
        if self._stream is None:
            return

        self._stream.disconnect()
        self._stream = None

    def receive_spike_channels(self) -> List[int]:
        if self._stream is None:
            raise RuntimeError("SpikeStream is not connected.")

        (_, more) = self._stream.receive_frame_number()

        if more:
            (_, more) = self._stream.receive_amplitudes()

        if more:
            return self._stream.receive_spike_channels()
        else:
            return []


@runtime_checkable
class SampleStream(Protocol):
    def connect(self) -> None:
        """Connect to a server producing signal data."""
        ...

    def disconnect(self) -> None:
        """Disconnect from the server producing signal data."""
        ...

    def sample(
        self,
        n_samples: int,
        channels: List[int],
    ) -> NDArray:
        """Retrieve signal data that are produced by the connected server.

        Parameters
        ----------
        n_sample : int
            Number of samples to be retrieved.
        channels : List[int]
            List of channels to be retrieved.

        Returns
        -------
        NDArray
            The retrieved signal data.
        """
        ...

    def __enter__(self) -> "SampleStream":
        """Call self `connect()` and return self.

        Returns
        -------
        SampleStream
            Self.
        """

        self.connect()
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        exception_traceback: Optional[TracebackType],
    ) -> bool:
        """Call self `disconnect()`."""

        self.disconnect()
        return False


class DebugSampleStream(SampleStream):
    """A class implementing `SampleStream` for debugging.

    This class generates random numbers to represent samples for each channel.
    """

    def __init__(self) -> None:
        """Initialize a new instance."""

        super().__init__()

        self._counter = 0

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def sample(
        self,
        n_samples: int,
        channels: List[int],
    ) -> NDArray:
        current = self._counter // 4
        if current == 1:
            self._counter = 0

        amp = -1 / (self._counter + 1)

        n_channels = len(channels)
        data = np.empty((n_samples, n_channels))

        for i in range(n_samples):
            data[i] = np.random.random(n_channels) * amp

        self._counter += 1

        return data


class MaxWellSampleStream(SampleStream):
    """A class implementing `SampleStream` to sample data via
    `MaxWellStream`.
    """

    def __init__(
        self,
        hostname: str = "localhost",
    ) -> None:
        """Instantiate a new instance.

        Parameters
        ----------
        hostname : str
            The hostname for the MaxWell server.
        """

        super().__init__()

        self._hostname = hostname
        self._stream: Optional[MaxWellStream] = None

    def connect(self) -> None:
        if self._stream is not None:
            return

        self._stream = MaxWellStream(self._hostname)
        self._stream.connect()

    def disconnect(self) -> None:
        if self._stream is None:
            return

        self._stream.disconnect()
        self._stream = None

    def sample(
        self,
        n_samples: int,
        channels: List[int],
    ) -> NDArray:
        if self._stream is None:
            raise RuntimeError("SampleStream is not connected.")

        map = np.zeros((n_samples, _MAX_N_FULL_SAMPLING_CHANNELS))

        for i in range(n_samples):
            (_, more) = self._stream.receive_frame_number()

            if more:
                (amplitudes, more) = self._stream.receive_amplitudes()
                map[i, :] = amplitudes

            if more:
                self._stream.receive_spike_events()

        return map[:, channels]


class SpikeCounter:
    """A class that counts received spikes per channel in the `SpikeStream`."""

    def __init__(
        self,
        stream: SpikeStream,
    ) -> None:
        """Initialize this instance.

        Parameters
        ----------
        stream : SpikeStream
            The `SpikeStream` instance.
        """

        self._stream = stream

    def detect(
        self,
        seconds: int,
        n_channels: int,
    ) -> List[int]:
        """Counts spikes detected within a specified time duration.

        Parameters
        ----------
        seconds : int
            The duration.
        n_channels : int
            The number of channels.

        Returns
        -------
        List[int]
            A list containing the number of spikes for each channel.
        """

        spike_counts = np.zeros((_MAX_N_FULL_SAMPLING_CHANNELS,), np.int_)

        try:
            self._stream.connect()
            for _ in range(seconds):
                all_spike_channels = []
                for _ in range(SAMPLING_FREQUENCY):
                    spike_channels = self._stream.receive_spike_channels()
                    all_spike_channels.extend(spike_channels)

                unique_spike_channels, spike_channel_counts = np.unique(
                    all_spike_channels, return_counts=True
                )
                if unique_spike_channels.size != 0:
                    spike_counts[unique_spike_channels] += spike_channel_counts

            return spike_counts[:n_channels].tolist()
        finally:
            self._stream.disconnect()
