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

import os
import numpy as np
from datetime import datetime

from maxwellio.array import MaxWellElectrodeArray, MockElectrodeArray
from maxwellio.saving import EmptyLocalSaving, MaxWellLocalSaving
from maxwellio.sampling import MAX_N_SAMPLING_CHANNELS

from config import DEBUG, MAX_STIM_EL_MAXWELL
from utils.logger import setup_logger
logger = setup_logger(__name__, debug=DEBUG)

_UPDATE_REC_DATE = False

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

        # Generate mapping conv channels to electrodes
        chan2el = np.zeros(MAX_N_SAMPLING_CHANNELS, dtype=np.int32)
        for mapping in cfg.mappings:
            chan2el[mapping.channel] = mapping.electrode

        elec_array.download()
        elec_array.offset()
        logger.info("Downloaded electrode array configuration")


        # Return electrode array and channel/electrode mapping
        return elec_array, chan2el

def init_maxwell_saver(fpath_cfg_file, dirpath_save):
    """Initiliaze Maxwell saver for recording"""
    fname = os.path.splitext(os.path.basename(fpath_cfg_file))[0]

    # Save with current date
    if _UPDATE_REC_DATE:
        fname = datetime.today().strftime('%Y%m%d_') + fname.split('_',1)[1] # update date

    fpath_save_no_ext = os.path.join(dirpath_save, fname)

    if not DEBUG:
        with open(fpath_save_no_ext + '.raw.h5', 'w') as f: 
            f.write(fpath_save_no_ext)
            f.close()
        maxwell_saving = EmptyLocalSaving()
    else:
        maxwell_saving = MaxWellLocalSaving()

    return maxwell_saving, fpath_save_no_ext