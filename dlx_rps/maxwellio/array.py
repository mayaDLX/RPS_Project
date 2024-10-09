# -*- coding: utf-8 -*-
# @title      MaxwellIO array
# @file       array.py
# @author     Atsuhiro Nabeta, Romain Beaubois
# @copyright
# SPDX-FileCopyrightText: ©2023 Atsuhiro Nabeta <atsuhiro.nabeta.lab@gmail.com>
# SPDX-FileCopyrightText: ©2024 Romain Beaubois <beaubois@iis.u-tokyo.ac.jp>
# SPDX-License-Identifier: MIT
#
# @brief
# Functions to control the electrode array of MaxOne through the API
# * electrode configuration from templates
# * electrode configuration from file
#
# @details
# > **01 Jan 2023** : file creation (AN)
# > **01 Jul 2024** : add file header (RB)
# > **01 Jul 2024** : add functions to load and get from config files (RB)

import math
from typing import (
    Iterable,
    List,
    Optional,
    Protocol,
    Tuple,
    runtime_checkable,
)

import maxlab
import maxlab.util
import numpy as np
from maxlab.chip import (
    Array,
    Core,
    StimulationUnit,
)
from maxlab.config import Config
from numpy.typing import NDArray

from maxwellio.stimulation import (
    EmptyStimulator,
    MaxWellStimulator,
    Stimulator,
)

N_MAP_COLUMNS = 220
"""Number of columns in the MaxWell electrode array."""

N_MAP_ROWS = 120
"""Number of rows in the MaxWell electrode array."""


@runtime_checkable
class ElectrodeArray(Protocol):
    """Protocol for wrapping the functionality of MaxLab's electrode array
    related classes.

    This protocol enables switching between a MaxWell system-connected
    implementation and an empty implementation for development purposes.
    """

    def initialize(self) -> None:
        """Wrap `maxlab.util.initialize()`."""
        ...

    def send_core_settings(self) -> None:
        """Wrap `maxlab.send(Core())`."""
        ...

    def offset(self) -> None:
        """Wrap `maxlab.util.offset()`."""
        ...

    def create_stimulator(self) -> Stimulator:
        """Create a new `Stimulator` instance.

        Returns
        -------
        Stimulator
            The created `Stimulator` instance.
        """
        ...

    def close(self) -> None:
        """Wrap `maxlab.chip.Array.close()`."""
        ...

    def reset(self) -> None:
        """Wrap `maxlab.chip.Array.reset()`."""
        ...

    def clear_selected_electrodes(self) -> None:
        """Wrap `maxlab.chip.Array.clear_selected_electrodes()`."""
        ...

    def select_electrodes(
        self,
        electrodes: Iterable[int],
    ) -> None:
        """Wrap `maxlab.chip.Array.select_electrodes()`.

        Parameters
        ----------
        electrodes : Iterable[int]
            Sampling (recording) electrodes.
        """
        ...

    def select_stimulation_electrodes(
        self,
        electrodes: Iterable[int],
    ) -> None:
        """Wrap `maxlab.chip.Array.select_stimulation_electrodes()`.

        Parameters
        ----------
        electrodes : Iterable[int]
            Stimulation electrodes.
        """
        ...

    def route(self) -> None:
        """Wrap `maxlab.chip.Array.route()`."""
        ...

    def connect_electrode_to_stimulation(
        self,
        electrode: int,
    ) -> None:
        """Wrap `maxlab.chip.Array.connect_electrode_to_stimulation()`.

        Parameters
        ----------
        electrode : int
            An electrode to be connected to a stimulation unit.
        """
        ...

    def query_stimulation_at_electrode(
        self,
        electrode: int,
    ) -> str:
        """Wrap `maxlab.chip.Array.query_stimulation_at_electrode()`.

        Parameters
        ----------
        electrode : int
            Electrodes to be queried.

        Returns
        -------
        str
            List of stimulation unit numbers.
        """
        ...

    def disconnect_electrode_from_stimulation(
        self,
        electrode: int,
    ) -> None:
        """Wrap `maxlab.chip.Array.disconnect_electrode_from_stimulation()`.

        Parameters
        ----------
        electrode : int
            An electrode to be disconnected from a stimulation unit.
        """
        ...

    def download(self) -> None:
        """Wrap `maxlab.chip.Array.download()`."""
        ...

    def power_up_stimulation_unit(
        self,
        unit: str,
    ) -> None:
        """Wrap `maxlab.send()` for power up,

        Parameters
        ----------
        unit : str
            Unit number.
        """
        ...

    def power_down_stimulation_unit(
        self,
        unit: str,
    ) -> None:
        """Wrap `maxlab.send()` for power down.

        Parameters
        ----------
        unit : str
            Unit number.
        """
        ...

    def load_config(
        self,
        fpath: str,
    ) -> None:
        """Wrap `maxlab.chip.Array.load_config()`.

        Parameters
        ----------
        fpath : str
            Path to electrode configuration file.
        """
        ...

    def get_config(
        self,
    ) -> Config:
        """Wrap `maxlab.chip.Array.get_config()`.

        Returns
        -------
        Config
            Config including electrode mapping class from Maxwell.
        """
        ...


class EmptyElectrodeArray(ElectrodeArray):
    """Empty implementation of `ElectrodeArray`."""

    def initialize(self) -> None:
        pass

    def send_core_settings(self) -> None:
        pass

    def offset(self) -> None:
        pass

    def create_stimulator(self) -> Stimulator:
        return EmptyStimulator()

    def close(self) -> None:
        pass

    def reset(self) -> None:
        pass

    def clear_selected_electrodes(self) -> None:
        pass

    def select_electrodes(
        self,
        electrodes: Iterable[int],
    ) -> None:
        pass

    def select_stimulation_electrodes(
        self,
        electrodes: Iterable[int],
    ) -> None:
        pass

    def route(self) -> None:
        pass

    def connect_electrode_to_stimulation(
        self,
        electrode: int,
    ) -> None:
        pass

    def query_stimulation_at_electrode(
        self,
        electrode: int,
    ) -> str:
        pass

    def disconnect_electrode_from_stimulation(
        self,
        electrode: int,
    ) -> None:
        pass

    def download(self) -> None:
        pass

    def power_up_stimulation_unit(
        self,
        unit: str,
    ) -> None:
        pass

    def power_down_stimulation_unit(
        self,
        unit: str,
    ) -> None:
        pass

    def load_config(
        self,
        fpath: str,
    ) -> None:
        pass

    def get_config(
        self,
    ) -> Config:
        return Config("0(5387)1872.5/420;1(11362)2485/892.5;")


class MockElectrodeArray(ElectrodeArray):
    """Mock implementation of `ElectrodeArray`."""

    def __init__(self) -> None:
        """Initialize a new instance."""

        super().__init__()
        self._selected_electrodes = []
        self._connected_stimulation_electrodes = []
        self._power_up_stimulation_units = []

    def initialize(self) -> None:
        pass

    def send_core_settings(self) -> None:
        pass

    def offset(self) -> None:
        pass

    def create_stimulator(self) -> Stimulator:
        return EmptyStimulator()

    def close(self) -> None:
        pass

    def reset(self) -> None:
        pass

    def clear_selected_electrodes(self) -> None:
        self._selected_electrodes = []

    def select_electrodes(
        self,
        electrodes: Iterable[int],
    ) -> None:
        self._selected_electrodes.extend(electrodes)

    def select_stimulation_electrodes(
        self,
        electrodes: Iterable[int],
    ) -> None:
        self._selected_electrodes.extend(electrodes)

    def route(self) -> None:
        pass

    def connect_electrode_to_stimulation(
        self,
        electrode: int,
    ) -> None:
        self._connected_stimulation_electrodes.append(electrode)

    def query_stimulation_at_electrode(
        self,
        electrode: int,
    ) -> str:
        index = self._connected_stimulation_electrodes.index(electrode)
        return str(index)

    def disconnect_electrode_from_stimulation(
        self,
        electrode: int,
    ) -> None:
        if electrode in self._connected_stimulation_electrodes:
            self._connected_stimulation_electrodes.remove(electrode)

    def download(self) -> None:
        pass

    def power_up_stimulation_unit(
        self,
        unit: str,
    ) -> None:
        self._power_up_stimulation_units.append(unit)

    def power_down_stimulation_unit(
        self,
        unit: str,
    ) -> None:
        if unit in self._power_up_stimulation_units:
            self._power_up_stimulation_units.remove(unit)

    # TODO: implement mock load config
    def load_config(
        self,
        fpath: str,
    ) -> None:
        pass

    def get_config(
        self,
    ) -> Config:
        """Generate dummy config (not hardware coherent)
        format: channel_id(electrode_id)x_pos/y_pos;"""
        map_list = []
        for channel_id in range(1024):
            # electrode_id = random.randint(0, 220*120-1)
            electrode_id = channel_id
            x_pos = electrode_id % 220
            y_pos = electrode_id // 220
            chan_mapping = (
                f"{channel_id}({electrode_id}){x_pos:.1f}/{y_pos:.1f}"
            )
            map_list.append(chan_mapping)
        mock_config = ";".join(map_list)
        return Config(mock_config)


class MaxWellElectrodeArray(ElectrodeArray):
    """A MaxWell system-connected implementation class for `ElectrodeArray`."""

    def __init__(self) -> None:
        """Initialize a new instance."""

        super().__init__()

        self._array = Array("stimulation")

    def initialize(self) -> None:
        maxlab.util.initialize()

    def send_core_settings(self) -> None:
        maxlab.send(Core())

    def offset(self) -> None:
        maxlab.util.offset()

    def create_stimulator(self) -> Stimulator:
        return MaxWellStimulator()

    def close(self) -> None:
        self._array.close()

    def reset(self) -> None:
        self._array.reset()

    def clear_selected_electrodes(self) -> None:
        self._array.clear_selected_electrodes()

    def select_electrodes(
        self,
        electrodes: Iterable[int],
    ) -> None:
        self._array.select_electrodes(electrodes)

    def select_stimulation_electrodes(
        self,
        electrodes: Iterable[int],
    ) -> None:
        self._array.select_stimulation_electrodes(electrodes)

    def route(self) -> None:
        self._array.route()

    def connect_electrode_to_stimulation(
        self,
        electrode: int,
    ) -> None:
        self._array.connect_electrode_to_stimulation(electrode)

    def query_stimulation_at_electrode(
        self,
        electrode: int,
    ) -> str:
        return self._array.query_stimulation_at_electrode(electrode)

    def disconnect_electrode_from_stimulation(
        self,
        electrode: int,
    ) -> None:
        self._array.disconnect_electrode_from_stimulation(electrode)

    def download(self) -> None:
        self._array.download()

    def power_up_stimulation_unit(
        self,
        unit: str,
    ) -> None:
        stimulation_unit = StimulationUnit(unit)
        stimulation_unit.power_up(True)
        stimulation_unit.connect(True)
        maxlab.send(stimulation_unit)

    def power_down_stimulation_unit(
        self,
        unit: str,
    ) -> None:
        stimulation_unit = StimulationUnit(unit)
        maxlab.send(stimulation_unit)

    def load_config(
        self,
        fpath: str,
    ) -> None:
        self._array.load_config(fpath)

    def get_config(
        self,
    ) -> Config:
        return self._array.get_config()


class ElectrodeMap:
    """A class that provides access to the electrode array."""

    def __init__(
        self,
        array_2d: NDArray[np.int_],
    ) -> None:
        """Initialize a new instance.

        Parameters
        ----------
        array_2d : NDArray[np.int_]
            A two-dimensional array of electrodes.
        """

        self._array_2d = array_2d
        self._array_1d = self._array_2d.ravel()
        self._n_rows = len(array_2d)
        self._n_columns = len(array_2d[0])
        self._n_channels = len(self._array_1d)

    @property
    def array_2d(self) -> NDArray[np.int_]:
        """Get the two-dimensional array of electrodes.

        Returns
        -------
        NDArray[np.int_]
            The two-dimensional array of electrodes.
        """

        return self._array_2d

    @property
    def array_1d(self) -> NDArray[np.int_]:
        """Get the one-dimensional array of electrodes.

        Returns
        -------
        NDArray[np.int_]
            The one-dimensional array of electrodes.
        """

        return self._array_1d

    @property
    def n_rows(self) -> int:
        """Get the number of rows.

        Returns
        -------
        int
            The number of rows.
        """

        return self._n_rows

    @property
    def n_columns(self) -> int:
        """Get the number of columns.

        Returns
        -------
        int
            The number of columns.
        """

        return self._n_columns

    @property
    def n_channels(self) -> int:
        """Get the number of channels.

        Returns
        -------
        int
            The number of channels.
        """

        return self._n_channels

    def get_x_y_by_channel(
        self,
        channel: int,
    ) -> Optional[Tuple[int, int]]:
        """Get X and Y coordinates by specifying a channel.

        Parameters
        ----------
        channel : int
            A target channel.

        Returns
        -------
        Optional[Tuple[int, int]]
            The X and Y coordinates for `channel` if exists; otherwise, `None`.

        Raises
        ------
        ValueError
            When `channel` exceeds `n_channels`.
        """

        if self._n_channels <= channel:
            raise ValueError(f"Out of range: {self._n_channels}")
        return (channel % self._n_columns, channel // self._n_columns)

    def get_channel_by_x_y(
        self,
        x: int,
        y: int,
    ) -> Optional[int]:
        """Get a channel number by specifying X and Y coordinates.

        Parameters
        ----------
        x : int
            X-coordinate value.
        y : int
            Y-coordinate value.

        Returns
        -------
        Optional[int]
            The channel number for `x` and `y` if exists; otherwise, `None`.

        Raises
        ------
        ValueError
            When `x` exceeds `n_columns`.
        ValueError
            When `y` exceeds `n_rows`.
        """

        if self._n_columns <= x:
            raise ValueError(f"Out of range: {(x)}")
        if self._n_rows <= y:
            raise ValueError(f"Out of range: {(y)}")
        return y * self._n_columns + x

    def get_x_y_by_electrode(
        self,
        electrode: int,
    ) -> Optional[Tuple[int, int]]:
        """Get X and Y coordinates by specifying an electrode ID.

        Parameters
        ----------
        electrode : int
            A target electrode ID.

        Returns
        -------
        Optional[Tuple[int, int]]
            The X and Y coordinates for `electrode` if exists; otherwise,
            `None`.
        """

        out = np.where(self._array_2d == electrode)
        if len(out[0]) == 0:
            return None
        # x, y
        return out[1][0], out[0][0]

    def get_electrode_by_x_y(
        self,
        x: int,
        y: int,
    ) -> int:
        """Get an electrode ID by specifying X and Y coordinates.

        Parameters
        ----------
        x : int
            X-coordinate value.
        y : int
            Y-coordinate value.

        Returns
        -------
        int
            The electrode ID for `x` and `y` if exists; otherwise, `None`.
        """

        return self._array_2d[y, x]

    def get_electrode_by_channel(
        self,
        channel: int,
    ) -> int:
        """Get an electrode ID by specifying a channel number.

        Parameters
        ----------
        channel : int
            A target channel number.

        Returns
        -------
        int
            The electrode ID for `channel`.

        Raises
        ------
        ValueError
            When `channel` exceeds `n_channels`.
        """

        x, y = self.get_x_y_by_channel(channel)
        return self.get_electrode_by_x_y(x, y)

    def get_channel_by_electrode(
        self,
        electrode: int,
    ) -> Optional[int]:
        """Get a channel number for specifying an electrode ID.

        Parameters
        ----------
        electrode : int
            The target electrode ID.

        Returns
        -------
        Optional[int]
            The channel number for `electrode` if exists; otherwise, `None`.
        """

        out = np.where(self._array_1d == electrode)
        if len(out[0]) == 0:
            return None
        return out[0][0]


class ElectrodeMapFactory(Protocol):
    """A factory class-based protocol for abstracting the instantiation of
    `ElectrodeMap`."""

    def create(self) -> ElectrodeMap:
        """Create a new `ElectrodeMap` instance.

        Returns
        -------
        ElectrodeMap
            The new `ElectrodeMap` instance.
        """
        ...


class SparseElectrodeMapFactory(ElectrodeMapFactory):
    """An implementation class of `ElectrodeMapFactory` that generates a
    sparsely populated `ElectrodeMap` with evenly spaced electrodes.
    """

    def __init__(
        self,
        interval: int = 5,
    ) -> None:
        """Initialize a new instance.

        Parameters
        ----------
        interval : int, optional
            The spacing between the electrodes used, by default 5
        """

        super().__init__()
        self._interval = interval

    def create(self) -> ElectrodeMap:
        center_offset = math.ceil(self._interval / 2)
        x_offsets = (
            (np.arange(0, N_MAP_COLUMNS, self._interval) + center_offset) - 1
        )[1:-1]

        y_offsets = (np.arange(0, N_MAP_ROWS, self._interval) - 1)[2:-1]
        map = [y * N_MAP_COLUMNS + x_offsets for y in y_offsets]

        return ElectrodeMap(np.array(map))


class Motor(Protocol):
    """A protocol for managing electrodes for motor."""

    @property
    def sampling_electrodes(self) -> Iterable[int]:
        """Get sampling electrodes.

        Returns
        -------
        Iterable[int]
            The sampling electrodes.
        """
        ...


class ChannelMotor(Motor):
    """An implementation class for `Motor` to resolve electrodes by
    channels.
    """

    def __init__(
        self,
        electrode_map: ElectrodeMap,
        channels: List[int],
    ) -> None:
        """Initialize a new instance.

        Parameters
        ----------
        electrode_map : ElectrodeMap
            An ElectrodeMap instance to be used to resolve electrodes.
        channels : List[int]
            A list of channels for this motor.
        """

        super().__init__()

        self._sampling_electrodes: List[int] = []
        for channel in channels:
            electrode = electrode_map.get_electrode_by_channel(channel)
            self._sampling_electrodes.append(electrode)

    @property
    def sampling_electrodes(self) -> Iterable[int]:
        return self._sampling_electrodes


class BoundsMotor(Motor):
    """An implementation class for `Motor` based on bounds."""

    def __init__(
        self,
        map: ElectrodeMap,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
    ) -> None:
        """Initialize a new instance.

        Parameters
        ----------
        map : ElectrodeMap
            A referenced `ElectrodeMap` instance.
        start_x : int
            X-coordinate of the start position of this bounds.
        start_y : int
            Y-coordinate of the start position of this bounds.
        end_x : int
            X-coordinate of the end position of this bounds.
        end_y : int
            Y-coordinate of the end position of this bounds.
        """

        super().__init__()

        sub_map = map.array_2d[start_y:end_y, start_x:end_x]
        self._sampling_electrodes: List[int] = sub_map.ravel().tolist()

    @property
    def sampling_electrodes(self) -> Iterable[int]:
        return self._sampling_electrodes


class Sensor(Protocol):
    """A protocol for managing electrodes for sensor."""

    @property
    def sampling_electrodes(self) -> Iterable[int]:
        """Get sampling electrodes.

        Returns
        -------
        Iterable[int]
            The sampling electrodes.
        """
        ...

    @property
    def stimulation_electrodes(self) -> Iterable[int]:
        """Get stimulation electrodes.

        Returns
        -------
        Iterable[int]
            The stimulation electrodes.
        """
        ...


class ChannelSensor(Sensor):
    """An implementation class for `Sensor` to resolve electrodes by
    channels.
    """

    def __init__(
        self,
        electrode_map: ElectrodeMap,
        channels: List[int],
    ) -> None:
        """Initialize a new instance.

        Parameters
        ----------
        electrode_map : ElectrodeMap
            An ElectrodeMap instance to be used to resolve electrodes.
        channels : List[int]
            A list of channels for this sensor.
        """

        super().__init__()

        self._sampling_electrodes: List[int] = []
        self._stimulation_electrodes: List[int] = []

        for channel in channels:
            sampling_electrode = electrode_map.get_electrode_by_channel(
                channel
            )
            self._sampling_electrodes.append(sampling_electrode)

            stimulation_electrode = sampling_electrode + 1 + N_MAP_COLUMNS
            self._stimulation_electrodes.append(stimulation_electrode)

    @property
    def sampling_electrodes(self) -> Iterable[int]:
        return self._sampling_electrodes

    @property
    def stimulation_electrodes(self) -> Iterable[int]:
        return self._stimulation_electrodes


class Patterns(Protocol):
    """A protocol for managing electrodes for patterns."""

    @property
    def n_patterns(self) -> int:
        """Get the number of patterns.

        Returns
        -------
        int
            The number of patterns.
        """
        ...

    def get_stimulation_electrodes(
        self,
        pattern: int,
    ) -> Iterable[int]:
        """Get stimulation electrodes used by the specified pattern.

        Parameters
        ----------
        pattern : int
            The target pattern.

        Returns
        -------
        Iterable[int]
            The stimulation electrodes used for `pattern`.
        """
        ...


class ChannelPatterns(Patterns):
    """An implementation class for `Patterns` to resolve pattern-specific
    stimulation electrodes from a list of pattern-specific channels.
    """

    def __init__(
        self,
        electrode_map: ElectrodeMap,
        pattern_channels_map: List[List[int]],
    ) -> None:
        """Initialize a new instance.

        Parameters
        ----------
        electrode_map : ElectrodeMap
            An ElectrodeMap instance to be used to reference electrodes.
        pattern_channels_map : List[List[int]]
            A list of pattern-specific channels.
        """

        super().__init__()

        self._pattern_electrodes_map: List[List[int]] = []

        for pattern in range(len(pattern_channels_map)):
            pattern_electrodes: List[int] = []
            pattern_channels = pattern_channels_map[pattern]
            for channel in pattern_channels:
                electrode = electrode_map.get_electrode_by_channel(channel)
                pattern_electrodes.append(electrode)

            self._pattern_electrodes_map.append(pattern_electrodes)

    @property
    def n_patterns(self) -> int:
        return len(self._pattern_electrodes_map)

    def get_stimulation_electrodes(
        self,
        pattern: int,
    ) -> Iterable[int]:
        return self._pattern_electrodes_map[pattern]


class ElectrodeArrayConfig:
    """A class responsible for managing an electrode array configuration."""

    def __init__(
        self,
        pattern_stimulation_electrodes_map: List[List[int]],
        motor_sampling_electrodes: List[int],
        sensor_sampling_electrodes: List[int],
        sensor_stimulation_electrodes: List[int],
    ) -> None:
        self._pattern_stimulation_electrodes_map = (
            pattern_stimulation_electrodes_map
        )
        self._motor_sampling_electrodes = motor_sampling_electrodes
        self._sensor_sampling_electrodes = sensor_sampling_electrodes
        self._sensor_stimulation_electrodes = sensor_stimulation_electrodes

        self._n_patterns = len(self._pattern_stimulation_electrodes_map)

        self._sampling_electrodes: NDArray[np.int_] = np.unique(
            np.sort(
                np.hstack(
                    (sensor_sampling_electrodes, motor_sampling_electrodes)
                )
            )
        )
        self._sampling_channels = list(range(len(self._sampling_electrodes)))

        self._motor_sampling_channels: List[int] = []
        for e in motor_sampling_electrodes:
            self._motor_sampling_channels.append(
                np.where(self._sampling_electrodes == e)[0][0]
            )

        self._sensor_sampling_channels: List[int] = []
        for e in sensor_sampling_electrodes:
            self._sensor_sampling_channels.append(
                np.where(self._sampling_electrodes == e)[0][0]
            )

    @classmethod
    def create(
        cls,
        patterns: Patterns,
        motor: Motor,
        sensor: Sensor,
    ) -> "ElectrodeArrayConfig":
        """Create a new `ElectrodeArrayConfig` instance.

        Parameters
        ----------
        patterns : Patterns
            Patterns.
        motor : Motor
            Motor.
        sensor : Sensor
            Sensor.

        Returns
        -------
        ElectrodeArrayConfig
            The created instance.
        """

        pattern_stimulation_electrodes_map: List[List[int]] = []
        for pattern in range(patterns.n_patterns):
            electrodes = patterns.get_stimulation_electrodes(pattern)
            pattern_stimulation_electrodes_map.append(electrodes)

        return ElectrodeArrayConfig(
            pattern_stimulation_electrodes_map,
            motor.sampling_electrodes,
            sensor.sampling_electrodes,
            sensor.stimulation_electrodes,
        )

    @property
    def motor_sampling_electrodes(self) -> Iterable[int]:
        return self._motor_sampling_electrodes

    @property
    def sensor_sampling_electrodes(self) -> Iterable[int]:
        return self._sensor_sampling_electrodes

    @property
    def sensor_stimulation_electrodes(self) -> Iterable[int]:
        return self._sensor_stimulation_electrodes

    @property
    def sampling_electrodes(self) -> Iterable[int]:
        """Get sampling electrodes.

        Returns
        -------
        Iterable[int]
            The sampling electrodes.
        """

        return self._sampling_electrodes

    @property
    def n_patterns(self) -> int:
        return self._n_patterns

    @property
    def sampling_channels(self) -> Iterable[int]:
        """Get the all sampling channels (`motor_sampling_channels` +
        `sensor_sampling_channels`).

        Returns
        -------
        Iterable[int]
            Sampling channels.
        """

        return self._sampling_channels

    @property
    def motor_sampling_channels(self) -> Iterable[int]:
        """Get the sampling channels for the motor.

        Returns
        -------
        Iterable[int]
            Sampling channels for the motor.
        """

        return self._motor_sampling_channels

    @property
    def sensor_sampling_channels(self) -> Iterable[int]:
        """Get the sampling channels for the sensor.

        Returns
        -------
        Iterable[int]
            Sampling channels for the sensor.
        """

        return self._sensor_sampling_channels

    def get_pattern_stimulation_electrodes(
        self,
        pattern: int,
    ) -> Iterable[int]:
        return self._pattern_stimulation_electrodes_map[pattern]


class ElectrodeArrayController:
    """A class for controlling the `ElectrodeArray` class."""

    def __init__(
        self,
        array: ElectrodeArray,
        config: ElectrodeArrayConfig,
    ) -> None:
        """Initialize a new instance.

        Parameters
        ----------
        array : ElectrodeArray
            A referenced `ElectrodeArray` instance.
        config : ElectrodeArrayConfig
            A referenced `ElectrodeArrayConfig` instance.
        """

        self._array = array
        self._config = config

        self._pattern_units_map: List[List[str]] = []
        self._sensor_units: List[str] = []
        self._random_sensor_units: List[str] = []
        self._random_sensor_electrodes: List[int] = []

    @property
    def sensor_units(self) -> List[str]:
        return self._sensor_units

    def route_electrodes(self) -> None:
        self._array.reset()
        self._array.clear_selected_electrodes()
        self._array.select_electrodes(self._config.sampling_electrodes)

        self._array.select_stimulation_electrodes(
            self._config.sensor_stimulation_electrodes
        )

        for pattern in range(self._config.n_patterns):
            self._array.select_stimulation_electrodes(
                self._config.get_pattern_stimulation_electrodes(pattern)
            )

        self._array.route()
        self._array.offset()

    def download(self) -> None:
        self._array.download()

    def prepare_all_pattern_stimulation_electrodes(self) -> None:
        self._pattern_units_map: List[List[str]] = []
        for pattern in range(self._config.n_patterns):
            units = self._connect_stimulation_electrodes(
                self._config.get_pattern_stimulation_electrodes(pattern)
            )
            self._pattern_units_map.append(units)

    def prepare_sensor_stimulation_electrodes(self) -> None:
        self._sensor_units: List[str] = self._connect_stimulation_electrodes(
            self._config.sensor_stimulation_electrodes
        )

    def enable_pattern_stimulation_units(
        self,
        pattern: int,
    ) -> None:
        units = self._pattern_units_map[pattern]
        self._power_up_stimulation_units(units)

    def disable_pattern_stimulation_units(
        self,
        pattern: int,
    ) -> None:
        units = self._pattern_units_map[pattern]
        self._power_down_stimulation_units(units)

        electrodes = self._config.get_pattern_stimulation_electrodes(pattern)
        self._disconnect_stimulation_electrodes(electrodes)

    def enable_sensor_stimulation_units(self) -> None:
        self._power_up_stimulation_units(self._sensor_units)

    def disable_sensor_stimulation_units(self) -> None:
        self._power_down_stimulation_units(self._sensor_units)
        self._disconnect_stimulation_electrodes(
            self._config.sensor_stimulation_electrodes
        )

    def enable_random_sensor_stimulation_units(
        self,
        size: int = 5,
    ) -> None:
        if not self._sensor_units:
            return

        unit_indices = list(range(len(self._sensor_units)))
        noise_indices = np.random.choice(unit_indices, size)

        self._random_sensor_units = [
            self.sensor_units[i] for i in noise_indices
        ]
        self._random_sensor_electrodes = (
            self._config.sensor_stimulation_electrodes
        )

        self._power_up_stimulation_units(self._random_sensor_units)

    def disable_random_sensor_stimulation_units(self) -> None:
        self._power_down_stimulation_units(self._random_sensor_units)
        self._disconnect_stimulation_electrodes(self._random_sensor_electrodes)
        self._random_sensor_units = []
        self._random_sensor_electrodes = []

    def _connect_stimulation_electrodes(
        self,
        electrodes: Iterable[int],
    ) -> List[str]:
        units: List[str] = []
        for electrode in electrodes:
            if unit := self._connect_stimulation_electrode(electrode):
                units.append(unit)

        return units

    def _connect_stimulation_electrode(
        self,
        electrode: int,
    ) -> str:
        self._array.connect_electrode_to_stimulation(electrode)
        return self._array.query_stimulation_at_electrode(electrode)

    def _disconnect_stimulation_electrodes(
        self,
        electrodes: Iterable[int],
    ) -> None:
        for electrode in electrodes:
            self._disconnect_stimulation_electrode(electrode)

    def _disconnect_stimulation_electrode(
        self,
        electrode: int,
    ) -> None:
        self._array.disconnect_electrode_from_stimulation(electrode)

    def _power_up_stimulation_units(
        self,
        units: Iterable[str],
    ) -> None:
        for unit in units:
            self._array.power_up_stimulation_unit(unit)

    def _power_down_stimulation_units(
        self,
        units: Iterable[str],
    ) -> None:
        for unit in units:
            self._array.power_down_stimulation_unit(unit)
