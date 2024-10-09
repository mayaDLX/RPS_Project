# -*- coding: utf-8 -*-
# @title      Activity Analysis thread
# @file       ActivityAnalysisThread.py
# @author     Romain Beaubois
# @date       10 Oct 2024
# @copyright
# SPDX-FileCopyrightText: © 2024 Romain Beauboois <refbeaubois@yahoo.com>
# SPDX-License-Identifier: MIT
#
# @brief
# * Analyze activity from Maxwell
# 
# @details

import time
import numpy as np
from PyQt5.QtCore import (QThread, pyqtSignal)

from config import DEBUG
from utils.logger import setup_logger
logger = setup_logger(__name__, debug=DEBUG)

class ActivityAnalysisThread(QThread):
    """Receive and analyze activity from Maxwell chip"""
    def __init__(self, rx_samples_rdy, chan2el:np.ndarray):
        """Initialize"""
        super().__init__()

        # Thread parameters
        self.stop_requested = False

        # Conversion array from channels to electrode index
        self.chan2el = chan2el # chan2el[channel] -> electrode
        logger.debug(f"Channel {0} is connected to electrode {chan2el[0]}")

        # Connect forward data to analysis when available
        rx_samples_rdy.connect(self.analyze_activity)

    def analyze_activity(self, rx_samples):
        """Analyze activity"""
        logger.debug("Received %d samples", len(rx_samples))

    def run(self):
        """Run thread"""
        logger.info("Start activity analysis ...")

        while not self.stop_requested:
            time.sleep(0.1)

    def stop(self):
        """Stop thread"""
        self.stop_requested = True