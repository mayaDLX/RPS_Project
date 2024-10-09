# -*- coding: utf-8 -*-
# @title      Maxwell read stream samples
# @file       MaxwellReadStreamThread.py
# @author     Romain Beaubois
# @date       10 Oct 2024
# @copyright
# SPDX-FileCopyrightText: © 2024 Romain Beauboois <refbeaubois@yahoo.com>
# SPDX-License-Identifier: MIT
#
# @brief
# * Read the stream of samples from Maxwell
# 
# @details

import numpy as np
from PyQt5.QtCore import (QThread, pyqtSignal)

import time
from config import DEBUG
from utils.logger import setup_logger
logger = setup_logger(__name__, debug=DEBUG)

from maxwellio.sampling import (MaxWellSampleStream, DebugSampleStream)

class MaxwellReadStreamThread(QThread):
    """Receive samples from Maxwell API"""
    rx_samples_rdy = pyqtSignal(np.ndarray)
    
    def __init__(self, n_samples, channels):
        """Initialize"""
        super().__init__()

        # Thread parameters
        self.stop_requested = False

        # Maxwell sample stream
        self.sample_stream = DebugSampleStream() if DEBUG else MaxWellSampleStream()
        self.n_samples = n_samples
        self.channels = channels

    def read_activity_maxwell(self):
        """Read samples from Maxwell API and emit when ready"""
        self.rx_samples_rdy.emit(self.sample_stream.sample(self.n_samples, self.channels))
        if DEBUG:
            time.sleep(self.n_samples/20000) # 20kHz sampling frequency

    def run(self):
        """Run thread"""
        self.sample_stream.connect()
        logger.info("Connected to Maxwell sample stream ...")
        try:
            while not self.stop_requested:
                self.read_activity_maxwell()
        finally:
            self.sample_stream.disconnect()

    def stop(self):
        """Stop thread"""
        self.stop_requested = True