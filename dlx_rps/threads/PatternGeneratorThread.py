# -*- coding: utf-8 -*-
# @title      Pattern generator thread
# @file       PatternGeneratorThread.py
# @author     Romain Beaubois
# @date       10 Oct 2024
# @copyright
# SPDX-FileCopyrightText: © 2024 Romain Beauboois <refbeaubois@yahoo.com>
# SPDX-License-Identifier: MIT
#
# @brief
# * Generate stimulation pattern for Maxwell
# 
# @details

import time
import numpy as np
from PyQt5.QtCore import (QThread, pyqtSignal)

from config import DEBUG, MAX_STIM_EL_MAXWELL, MAX_PARAMS_STIM_MAXWELL, PARAMS_STIM_MAXWELL
from utils.logger import setup_logger

logger = setup_logger(__name__, debug=DEBUG)

class PatternGeneratorThread(QThread):
    """Send stimulation to Maxwell"""
    stim_flag_data = pyqtSignal(np.ndarray)

    def __init__(self):
        """Initialize"""
        super().__init__()

        # Thread parameters
        self.stop_requested = False

        # Dummy stimulation pattern
        # for genericity all electrodes can have different amp/freq
        # but current version only support identical amp/freq for all electrodes
        # the handling of different protocol per stimulation unit in dynamic is
        # a bit of a pain
        self.dummy_stim_pattern = np.zeros((MAX_STIM_EL_MAXWELL, MAX_PARAMS_STIM_MAXWELL))
        self.dummy_stim_pattern[:,PARAMS_STIM_MAXWELL['EL_ID']] = np.arange(MAX_STIM_EL_MAXWELL)
        self.dummy_stim_pattern[:,PARAMS_STIM_MAXWELL['STIM_AMP_MV']] = 400
        self.dummy_stim_pattern[:,PARAMS_STIM_MAXWELL['STIM_FREQ_HZ']] = 100
        self.posture = None

    def update_posture(self, posture):
        self.posture = posture

    def send_stim_pattern(self):
        self.stim_flag_data.emit(self.dummy_stim_pattern)
        logger.debug("Send stimulation pattern ...")

    def run(self):
        """Run thread"""
        logger.info("Start pattern generation ...")

        while not self.stop_requested:
            self.send_stim_pattern()
            time.sleep(0.5)

    def stop(self):
        """Stop thread"""
        self.stop_requested = True