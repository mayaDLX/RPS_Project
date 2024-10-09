# -*- coding: utf-8 -*-
# @title      Maxwell stimulation
# @file       MaxwellStimulationThread.py
# @author     Romain Beaubois
# @date       10 Oct 2024
# @copyright
# SPDX-FileCopyrightText: © 2024 Romain Beauboois <refbeaubois@yahoo.com>
# SPDX-License-Identifier: MIT
#
# @brief
# * Send stimulation to Maxwell
# 
# Stimulation data should be sent as a numpy array:
# np.zeros((NB_STIM_EL, MAX_PARAMS_STIM_MAXWELL))
# stim_data[0,0] -> channel id
# stim_data[0,1] -> stimulation amplitude
# stim_data[0,2] -> stimulation frequency
# 
# @details

import time
import numpy as np
from PyQt5.QtCore import (QThread, pyqtSignal)

from config import DEBUG, MAX_STIM_CHANNELS_MAXWELL, MAX_PARAMS_STIM_MAXWELL, PARAMS_STIM_MAXWELL
from utils.logger import setup_logger
logger = setup_logger(__name__, debug=DEBUG)

from maxlab.config import Config
from maxwellio.stimulation import (Stimulator, MaxWellStimulator, EmptyStimulator)
from maxwellio.stimulation import (PulseStreamStimulatorBuilder)
from maxwellio.array import (ElectrodeArray)

INDEPENDENT_STIM_SOURCES = False

class MaxwellStimulationThread(QThread):
    """Send stimulation to Maxwell"""    
    def __init__(self, elec_array:ElectrodeArray, cfg_elec_array:Config, stim_flag_data, stim_chan, stim_amp_mv, stim_freq_hz):
        """Initialize"""
        super().__init__()

        # Thread parameters
        self.stop_requested = True

        # Maxwell stimulation
        self.cfg_elec_array = cfg_elec_array # mapping configuration object
        self.elec_array = elec_array # electrode array object
        self.unified_stimulator = self.init_unified_stimulation(stim_chan, stim_amp_mv, stim_freq_hz)

        # Connect signals
        stim_flag_data.connect(self.stimulate_maxwell)

    def stimulate_maxwell(self, stim_data):
        """Stimulate channels"""
        if len(stim_data) > MAX_STIM_CHANNELS_MAXWELL:
            logger.warning("Too many stimulation channels required, cropped list to %d", MAX_STIM_CHANNELS_MAXWELL)
            stim_data = stim_data[:MAX_STIM_CHANNELS_MAXWELL,:]

        if INDEPENDENT_STIM_SOURCES:
            for chan, amp, freq in stim_data:
                stimulation_units = []

                for el in self.cfg_elec_array.get_channels_for_electrodes(chan):
                    self.elec_array.connect_electrode_to_stimulation( el )
                    stim = self.elec_array.query_stimulation_at_electrode( el )
                    if stim:
                        stimulation_units.append( stim )
                    else:
                        logger.warning("No stimulation channel can connect to electrode: %d", el)

                for stimulation_unit in stimulation_units:
                    self.elec_array.power_up_stimulation_unit(stimulation_unit)

                # Create stimulation source
                self.indep_stimulator = EmptyStimulator() if DEBUG else MaxWellStimulator()
                _PULSE_PHASE_US = 200
                _NB_PULSES      = 4
                stim_builder = PulseStreamStimulatorBuilder(
                    period_us    = 2*_PULSE_PHASE_US,
                    amplitude_mv = stim_data['STIM_AMP_MV'],
                    offset       = 0.0,
                    nb_pulses    = _NB_PULSES,
                    ipi_ms       = 1e3/1e3/stim_data['STIM_FREQ_HZ'],
                    duty_cycle   = 0.5,
                )
                stim_builder.build(self.indep_stimulator)
                self.indep_stimulator.stimulate()
                logger.info("Sent independent stimulation")
        else:
            self.unified_stimulator.stimulate()
            logger.info("Sent unified stimulation")

    def init_unified_stimulation(self, stim_chan, stim_amp_mv, stim_freq_hz) -> Stimulator:
        """Initial stimulation electrodes in case of fixed stimulation electrode configuration"""        
        # Setting up stimulation units once
        if len(stim_chan) > MAX_STIM_CHANNELS_MAXWELL:
            logger.warning("Too many stimulation channels required, cropped list to %d", MAX_STIM_CHANNELS_MAXWELL)
            stim_chan = stim_chan[:MAX_STIM_CHANNELS_MAXWELL]

        stimulation_units = []
        for el in self.cfg_elec_array.get_channels_for_electrodes(stim_chan):
            self.elec_array.connect_electrode_to_stimulation( el )
            stim = self.elec_array.query_stimulation_at_electrode( el )
            if stim:
                stimulation_units.append( stim )
            else:
                logger.warning("No stimulation channel can connect to electrode: %d", el)

        for stimulation_unit in stimulation_units:
            self.elec_array.power_up_stimulation_unit(stimulation_unit)

        logger.info("Connected stimulation electrodes and powered up units")

        # Create stimulation source
        stimulator      = EmptyStimulator() if DEBUG else MaxWellStimulator()
        _PULSE_PHASE_US = 200
        _NB_PULSES      = 4
        stim_builder = PulseStreamStimulatorBuilder(
            period_us    = 2*_PULSE_PHASE_US,
            amplitude_mv = stim_amp_mv,
            offset       = 0.0,
            nb_pulses    = _NB_PULSES,
            ipi_ms       = 1e3/stim_freq_hz,
            duty_cycle   = 0.5,
        )
        stim_builder.build(stimulator)

        return stimulator

    def run(self):
        """Run thread"""
        logger.info("Ready Maxwell stimualtion sending ...")

        while not self.stop_requested:
            time.sleep(0.1)

    def stop(self):
        """Stop thread"""
        self.stop_requested = True