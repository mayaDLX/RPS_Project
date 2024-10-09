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
#   * Fixed stimulation has always same protocol and stim electrodes
#   * Dynamic stimulation have different protocol and stim electrodes,
#     but all electrodes stimulated share the same protocol
# 
# Stimulation data should be sent as a numpy array:
# np.zeros((NB_STIM_EL, MAX_PARAMS_STIM_MAXWELL))
# stim_data[0,0] -> electrode id
# stim_data[0,1] -> stimulation amplitude
# stim_data[0,2] -> stimulation frequency
# 
# @details

import time
import numpy as np
from PyQt5.QtCore import (QThread, pyqtSignal)

from config import DEBUG, MAX_STIM_EL_MAXWELL, MAX_PARAMS_STIM_MAXWELL, PARAMS_STIM_MAXWELL
from utils.logger import setup_logger
logger = setup_logger(__name__, debug=DEBUG)

from maxwellio.stimulation import (Stimulator, MaxWellStimulator, EmptyStimulator)
from maxwellio.stimulation import (PulseStreamStimulatorBuilder)
from maxwellio.array import (ElectrodeArray)

_FIXED_STIM_EL = False # Fixed stimulation connection and protocol for all stim electrodes

class MaxwellStimulationThread(QThread):
    """Send stimulation to Maxwell"""    
    def __init__(self, elec_array:ElectrodeArray, stim_flag_data, stim_el, stim_amp_mv, stim_freq_hz):
        """Initialize"""
        super().__init__()

        # Thread parameters
        self.stop_requested = True

        # Maxwell stimulation
        self.elec_array = elec_array # electrode array object
        self.fixed_stimulator, self.fixed_stim_units = self.init_fixed_stimulation(stim_el, stim_amp_mv, stim_freq_hz)
        self.dynamic_stim_units = []

        # Connect signals
        stim_flag_data.connect(self.stimulate_maxwell)

    def stimulate_maxwell(self, stim_data):
        """Stimulate channels"""
        # Handle exception when too many stimulation electrodes specified
        if len(stim_data) > MAX_STIM_EL_MAXWELL:
            logger.warning("Too many stimulation channels required, cropped list to %d", MAX_STIM_EL_MAXWELL)
            stim_data = stim_data[:MAX_STIM_EL_MAXWELL,:]

        # Dynamic electrode stimulation (stimulation electrode may change location and protocol)
        if not _FIXED_STIM_EL:
            amp_mv  = stim_data[0, PARAMS_STIM_MAXWELL['STIM_AMP_MV']]  # for now, same stim for all selected electrodes
            freq_hz = stim_data[0, PARAMS_STIM_MAXWELL['STIM_FREQ_HZ']] # for now, same stim for all selected electrodes
            
            # Power off all units
            for stim_unit in self.dynamic_stim_units:
                self.elec_array.power_down_stimulation_unit(stim_unit)

            # Route new electrodes and power up stimulatio units
            for el in stim_data[:,PARAMS_STIM_MAXWELL['EL_ID']].astype(int):
                self.elec_array.connect_electrode_to_stimulation( el )
                stim = self.elec_array.query_stimulation_at_electrode( el )
                if stim:
                    self.dynamic_stim_units.append( stim )
                else:
                    logger.warning("No stimulation channel can connect to electrode: %d", el)

                self.elec_array.power_up_stimulation_unit(stim)

            # Create new stimulation protocol (shared by all stim electrodes)
            self.dynamic_stimulator = EmptyStimulator() if DEBUG else MaxWellStimulator()
            _PULSE_PHASE_US = 200
            _NB_PULSES      = 4
            stim_builder = PulseStreamStimulatorBuilder(
                period_us    = 2*_PULSE_PHASE_US,
                amplitude_mv = amp_mv,
                offset       = 0.0,
                nb_pulses    = _NB_PULSES,
                ipi_ms       = 1e3/freq_hz,
                duty_cycle   = 0.5,
            )
            stim_builder.build(self.dynamic_stimulator)

            # Send stimulation trigger
            self.dynamic_stimulator.stimulate()
            logger.debug("Sent dynamic electrode stimulation")
        else:
            # Parse stimulation units to power up amongst the fixed electrodes
            selected_stim_units = [self.elec_array.query_stimulation_at_electrode(int(el)) for el in stim_data[:, PARAMS_STIM_MAXWELL['EL_ID']]]

            # Power up/down stimulation units
            for stim_unit in self.fixed_stim_units:
                if stim_unit in selected_stim_units:
                    self.elec_array.power_up_stimulation_unit(stim_unit)
                else:
                    self.elec_array.power_down_stimulation_unit(stim_unit)

            # Send stimulation trigger
            self.fixed_stimulator.stimulate()
            logger.debug("Sent fixed electrode stimulation")

    def init_fixed_stimulation(self, stim_el, stim_amp_mv, stim_freq_hz) -> Stimulator:
        """Initial stimulation electrodes in case of fixed stimulation electrode configuration"""        
        # Setting up stimulation units once
        if len(stim_el) > MAX_STIM_EL_MAXWELL:
            logger.warning("Too many stimulation channels required, cropped list to %d", MAX_STIM_EL_MAXWELL)
            stim_el = stim_el[:MAX_STIM_EL_MAXWELL]

        stimulation_units = []
        for el in stim_el:
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

        return stimulator, stimulation_units

    def run(self):
        """Run thread"""
        logger.info("Ready Maxwell stimualtion sending ...")

        while not self.stop_requested:
            time.sleep(0.1)

    def stop(self):
        """Stop thread"""
        self.stop_requested = True