# -*- coding: utf-8 -*-
# @title      MaxwellIO stimulation
# @file       stimulation.py
# @author     Atsuhiro Nabeta, Romain Beaubois
# @copyright
# SPDX-FileCopyrightText: ©2023 Atsuhiro Nabeta <atsuhiro.nabeta.lab@gmail.com>
# SPDX-FileCopyrightText: ©2024 Romain Beaubois <beaubois@iis.u-tokyo.ac.jp>
# SPDX-License-Identifier: MIT
#
# @brief
# Functions to control stimulation of MaxOne through the API
#   * Generate stimulation sequences for different patterns
#   * Export stimulation triggers to .raw.h5
#
# @details
# > **01 Jan 2023** : file creation (AN)
# > **01 Jul 2024** : add file header (RB)
# > **01 Jul 2024** : add new class for stream of pulses stimulation (RB)
# > **01 Jul 2024** : fix stimulation event export in .raw.h5 from v24.1 (RB)

from typing import Protocol

import maxlab
import maxlab.util
import numpy as np
from maxlab.chip import DAC
from maxlab.system import (
    DelaySamples,
    Event,
)
from scipy.stats import truncnorm

from maxwellio.sampling import SAMPLING_FREQUENCY

_DAC_CODE_RESOLUTION = 2.9
"""DAC code resolution (mV)."""

_DAC_CODE_RANGE = 2**10
"""Range for DAC code = 10 bits = 2^10 bits = 1024 bits."""

_DAC_CODE_ZERO = int(_DAC_CODE_RANGE / 2)
"""DAC code for 0 mV = 512 bits."""

MAX_AMPLITUDE = int(_DAC_CODE_ZERO * _DAC_CODE_RESOLUTION)
"""Max amplitude (mV) = int(512 * 2.9)."""

MIN_AMPLITUDE = -MAX_AMPLITUDE
"""Min amplitude (mV) = -int(512 * 2.9)."""


def _to_dac_code(mV: float) -> int:
    """Convert a voltage (mV) to the DAC code.

    Parameters
    ----------
    mV : float
        Voltage (mV).

    Returns
    -------
    int
        The DAC code.
    """

    mV = min(mV, MAX_AMPLITUDE)
    mV = max(mV, MIN_AMPLITUDE)

    # DAC in voltage mode is inverter amplifier, so (-) to make (+)
    return _DAC_CODE_ZERO - round(mV / _DAC_CODE_RESOLUTION)


def _frequency_to_samples(frequency: float) -> int:
    """Convert frequency to the number of samples.

    Parameters
    ----------
    frequency : float
        The frequency.

    Returns
    -------
    int
        The number of samples.
    """

    return int(SAMPLING_FREQUENCY / frequency)


def _period_to_samples(period: float) -> int:
    """Convert period to the number of samples.

    Parameters
    ----------
    period : float
        The period in seconds.

    Returns
    -------
    int
        The number of samples.
    """

    return int(SAMPLING_FREQUENCY * period)


class Stimulator(Protocol):
    """A protocol for wrapping the MaxLab `Sequence` for stimulation.

    This protocol enables switching between a MaxWell system-connected
    implementation and an empty implementation for development purposes.
    """

    def add(
        self,
        mV: float,
        n_samples: int,
    ) -> None:
        """Add stimulation.

        Parameters
        ----------
        mV : float
            Voltage (mV).
        n_samples : int
            Number of samples to stimulate.
        """
        ...

    def add_event_flag(
        self,
        mV: float,
        phase: float,
    ) -> None:
        """Add event flag to export stimulation trigger.

        Parameters
        ----------
        mV : float
            Voltage (mV).
        phase : float
            Just for compatibility with default Matlab, can be anything.
        """
        ...

    def stimulate(self) -> None:
        """Stimulate electrodes."""
        ...


class StimulatorBuilder(Protocol):
    """A protocol to build a `Stimulator` instance."""

    def build(
        self,
        stimulator: Stimulator,
    ) -> None:
        """Build Stimulator instance.

        Parameters
        ----------
        stimulator : Stimulator
            A Stimulator instance to be built.
        """
        ...


class EmptyStimulator(Stimulator):
    """Empty implementation of `Stimulator`."""

    def add(
        self,
        mV: float,
        n_samples: int,
    ) -> None:
        pass

    def add_event_flag(
        self,
        mV: float,
        phase: float,
    ) -> None:
        pass

    def stimulate(self) -> None:
        pass


class MaxWellStimulator(Stimulator):
    """A MaxWell system-connected implementation class for `Stimulator`."""

    def __init__(self) -> None:
        """Initialize a new instance."""

        super().__init__()

        self._sequence = maxlab.Sequence()
        self._event_counter = 1

    def add(
        self,
        mV: float,
        n_samples: int,
    ) -> None:
        self._sequence.append(DAC(0, _to_dac_code(mV)))
        self._sequence.append(DelaySamples(n_samples))

    def add_event_flag(
        self,
        mV: float,
        phase: float,
    ) -> None:
        self._sequence.append(
            Event(
                0,
                1,
                self._event_counter,
                f"amplitude {mV} phase {phase}",
            )
        )
        self._event_counter += 1

    def stimulate(self) -> None:
        self._sequence.send()


class PulseStreamStimulatorBuilder(StimulatorBuilder):
    """A class to build stream of pulses wave."""

    def __init__(
        self,
        period_us: float = 1,
        amplitude_mv: float = 1,
        offset: float = 1,
        duty_cycle: float = 0.5,
        nb_pulses: int = 5,
        ipi_ms: float = 1,
    ) -> None:
        """_summary_

        Parameters
        ----------
        period_us : float, optional
            Period in microseconds, by default 1.
        amplitude_mv : float, optional
            Amplitude in mV, by default 1.
        offset : float, optional
            Offset, by default 1.
        duty_cycle : float, optional
            Duty cycle, by default 0.5 (50%).
        nb_pulses : float, optional
            Number of pulses, by default 5.
        ipi_ms : float, optional
            Inter pulse interval by default 1.
        """

        super().__init__()

        self.period_us = period_us
        self.amplitude_mv = amplitude_mv
        self.offset = offset
        self.duty_cycle = duty_cycle
        self.nb_pulses = nb_pulses
        self.ipi_ms = ipi_ms

    def build(
        self,
        stimulator: Stimulator,
    ) -> None:
        # The number of samples in the frequency
        samples_in_cycle = _period_to_samples(self.period_us * 1e-6)
        # Amplitude for high state
        high = self.offset + self.amplitude_mv
        # Amplitude for low state
        low = self.offset - self.amplitude_mv
        # The number of samples in high state
        n_samples_in_high = int(samples_in_cycle * self.duty_cycle)
        # The number of samples in low state
        n_samples_in_low = samples_in_cycle - n_samples_in_high
        # Amplitude no stimulation
        no_stim = self.offset
        # The number of samples between pulses
        n_samples_inter_pulse = _period_to_samples(self.ipi_ms * 1e-3)

        # Just one stimulation trigger at the beginning of pulse stream
        stimulator.add_event_flag(self.amplitude_mv, self.period_us)
        for _ in range(self.nb_pulses):
            stimulator.add(high, n_samples_in_high)
            stimulator.add(low, n_samples_in_low)
            stimulator.add(no_stim, n_samples_inter_pulse)


class SquareWaveStimulatorBuilder(StimulatorBuilder):
    """A class to build square wave."""

    def __init__(
        self,
        frequency: float = 1,
        amplitude: float = 1,
        offset: float = 1,
        duty_cycle: float = 0.5,
    ) -> None:
        """_summary_

        Parameters
        ----------
        frequency : float, optional
            Frequency, by default 1.
        amplitude : float, optional
            Amplitude, by default 1.
        offset : float, optional
            Offset, by default 1.
        duty_cycle : float, optional
            Duty cycle, by default 0.5 (50%).
        """

        super().__init__()

        self.frequency = frequency
        self.amplitude = amplitude
        self.offset = offset
        self.duty_cycle = duty_cycle

    def build(
        self,
        stimulator: Stimulator,
    ) -> None:
        # The number of samples in the frequency
        samples_in_cycle = _frequency_to_samples(self.frequency)
        # Amplitude for high state
        high = self.offset + self.amplitude
        # Amplitude for low state
        low = self.offset - self.amplitude
        # The number of samples in high state
        n_samples_in_high = int(samples_in_cycle * self.duty_cycle)
        # The number of samples in low state
        n_samples_in_low = samples_in_cycle - n_samples_in_high

        stimulator.add_event_flag(self.amplitude, 1 / self.frequency)
        stimulator.add(high, n_samples_in_high)
        stimulator.add(low, n_samples_in_low)


class SineWaveStimulatorBuilder(StimulatorBuilder):
    """A class to build sine wave."""

    def __init__(
        self,
        frequency: float = 1,
        amplitude: float = 1,
        offset: float = 1,
    ) -> None:
        """_summary_

        Parameters
        ----------
        frequency : float, optional
            Frequency, by default 1.
        amplitude : float, optional
            Amplitude, by default 1.
        offset : float, optional
            Offset, by default 1.
        """

        super().__init__()

        self.frequency = frequency
        self.amplitude = amplitude
        self.offset = offset

    def build(
        self,
        stimulator: Stimulator,
    ) -> None:
        # The number of samples in the frequency
        samples_in_cycle = _frequency_to_samples(self.frequency)
        # Time points
        t = np.linspace(0, 1, samples_in_cycle)
        # Sine amplitudes
        y = np.sin(t)

        stimulator.add_event_flag(self.amplitude, 1 / self.frequency)
        for i in range(samples_in_cycle):
            amplitude = y[i] * self.amplitude + self.offset
            stimulator.add(amplitude, 1)


class GaussianNoiseWaveStimulatorBuilder(StimulatorBuilder):
    """A class to build Gaussian (normally distributed) noise wave."""

    def __init__(
        self,
        frequency: float = 1,
        amplitude: float = 1,
        mu: float = 0,
        sigma: float = 1,
    ) -> None:
        """_summary_

        Parameters
        ----------
        frequency : float, optional
            Frequency, by default 1.
        amplitude : float, optional
            Amplitude, by default 1.
        mu : float, optional
            Mean, by default 0.
        sigma : float, optional
            Standard deviation, by default 1.
        """

        super().__init__()

        self.frequency = frequency
        self.amplitude = amplitude
        self.mu = mu
        self.sigma = sigma

    def build(
        self,
        stimulator: Stimulator,
    ) -> None:
        # The number of samples in the frequency
        samples_in_cycle = _frequency_to_samples(self.frequency)

        # Use truncated normal distribution
        voltages = truncnorm.rvs(
            -self.amplitude,
            self.amplitude,
            loc=self.mu,
            scale=self.sigma,
            size=samples_in_cycle,
        )

        stimulator.add_event_flag(self.amplitude, 1 / self.frequency)
        for i in range(samples_in_cycle):
            voltage = voltages[i]
            stimulator.add(voltage, 1)


class SynapticNoiseWaveStimulatorBuilder(StimulatorBuilder):
    """A class to build synaptic noise wave (Destexhe article based on
    Ornstein-Uhlenbeck process).
    """

    def __init__(
        self,
        frequency: float = 1,
        amplitude: float = 1,
        mu: float = 0,
        sigma: float = 1,
        theta: float = 1,
    ) -> None:
        """_summary_

        Parameters
        ----------
        frequency : float, optional
            Frequency, by default 1.
        amplitude : float, optional
            Amplitude, by default 1.
        mu : float, optional
            Mean, by default 0.
        sigma : float, optional
            Standard deviation, by default 1.
        theta : float, optional
            Theta, by default 1.
        """

        super().__init__()

        self.frequency = frequency
        self.amplitude = amplitude
        self.mu: float = 0
        self.sigma: float = 0
        self.theta: float = 1

    def build(
        self,
        stimulator: Stimulator,
    ) -> None:
        # Time step (ms)
        dt = 1e3 / SAMPLING_FREQUENCY
        # The number of samples in the frequency
        samples_in_cycle = _frequency_to_samples(self.frequency)
        # Redefine for just readability
        mu = self.mu
        sigma = self.sigma
        theta = self.theta
        # Initial value
        previous = mu

        stimulator.add_event_flag(self.amplitude, 1 / self.frequency)
        for _ in range(samples_in_cycle):
            dw = np.sqrt(dt) * np.random.normal()
            x = previous + theta * dt * (mu - previous) + sigma * dw
            previous = x
            voltage = np.clip(x, -self.amplitude, self.amplitude)
            stimulator.add(voltage, 1)
