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

from config import DEBUG, MAX_STIM_CHANNELS_MAXWELL, MAX_PARAMS_STIM_MAXWELL
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

    def send_stim_pattern(self):
        self.stim_flag_data.emit(np.zeros((MAX_STIM_CHANNELS_MAXWELL, MAX_PARAMS_STIM_MAXWELL)))
        logger.info("Send stimulation pattern ...")

    def run(self):
        """Run thread"""
        logger.info("Start pattern generation ...")

        while not self.stop_requested:
            time.sleep(0.5)
            self.send_stim_pattern()

    def stop(self):
        """Stop thread"""
        self.stop_requested = True