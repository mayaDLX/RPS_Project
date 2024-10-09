# -*- coding: utf-8 -*-
# @title      Maxwell setup functions
# @file       maxwell_setup.py
# @author     Romain Beaubois
# @date       10 Oct 2024
# @copyright
# SPDX-FileCopyrightText: © 2024 Romain Beauboois <refbeaubois@yahoo.com>
# SPDX-License-Identifier: MIT
#
# @brief
# * Provide basic functions to setup Maxwell array
# 
# @details

from maxwellio.array import ElectrodeArray, MaxWellElectrodeArray, MockElectrodeArray

from config import DEBUG, MAX_STIM_CHANNELS_MAXWELL
from utils.logger import setup_logger
logger = setup_logger(__name__, debug=DEBUG)

def init_maxwell_array(fpath_cfg_elec_array):
        """Initialize Maxwell array and stim electrodes"""
        elec_array = MockElectrodeArray() if DEBUG else MaxWellElectrodeArray()

        # Initialize system into a defined state
        elec_array.initialize()
        logger.info("Initiliazed electrode array")

        elec_array.send_core_settings()
        elec_array.reset()
        logger.info("Reset electrode array")

        elec_array.load_config(fpath_cfg_elec_array)
        cfg = elec_array.get_config()
        logger.info("Load electrode array configuration from file:%s", fpath_cfg_elec_array)

        elec_array.download()
        elec_array.offset()
        logger.info("Downloaded electrode array configuration")

        # Return electrode array and channel/electrode mapping
        return elec_array, cfg

def connect_stimulation_el(stim_el:list, elec_array:ElectrodeArray):
        if len(channels) > MAX_STIM_CHANNELS_MAXWELL:
            logger.warning("Too many stimulation channels required, cropped list to %d", MAX_STIM_CHANNELS_MAXWELL)
            channels = channels[:MAX_STIM_CHANNELS_MAXWELL]
        
        # Setting up stimulation units
        stimulation_units = []
        for el in stim_el:
            elec_array.connect_electrode_to_stimulation( el )
            stim = elec_array.query_stimulation_at_electrode( el )
            if stim:
                stimulation_units.append( stim )
            else:
                logger.warning("No stimulation channel can connect to electrode: %d", el)

        for stimulation_unit in stimulation_units:
            elec_array.power_up_stimulation_unit(stimulation_unit)

        logger.info("Connected stimulation electrodes and powered up units")

        return stimulation_units