# -*- coding: utf-8 -*-
# @title      Main script DLX RPS project
# @file       runStimProc.py
# @author     Romain Beaubois
# @date       10 Oct 2024
# @copyright
# SPDX-FileCopyrightText: © 2024 Romain Beauboois <refbeaubois@yahoo.com>
# SPDX-License-Identifier: MIT
#
# @brief
# * MaxwellReadStreamThread: read sample stream from Maxwell and forward data with pyqtsignal
# * MaxwellStimulationThread: receive pattern via pyqtsignal and stimulation Maxwell
# * PatternGeneratorThread: generate patterns from hand gestures
# * ActivityAnalysisThread: analyze data and provide output results
# * (TODO) Add data recording
# 
# @details

# General
import os, sys
import numpy as np
import time
from config import DEBUG, MAX_STIM_CHANNELS_MAXWELL, MAX_PARAMS_STIM_MAXWELL

# pyqt
from PyQt5.QtWidgets    import (QApplication)
from PyQt5.QtCore       import (QThread, pyqtSignal, QTimer)

# Maxwell I/O
from maxwellio.saving import (MaxWellLocalSaving)
from maxwellio.array import (MockElectrodeArray, MaxWellElectrodeArray, N_MAP_COLUMNS)
from maxwellio.stimulation import (MaxWellStimulator, PulseStreamStimulatorBuilder, SquareWaveStimulatorBuilder, EmptyStimulator)

# Configuration files and setup
from utils.load_cfg import load_yaml_configuration_file
from utils.maxwell_setup import init_maxwell_array, connect_stimulation_el

# Logging
from utils.logger import setup_logger
logger = setup_logger(__name__, debug=DEBUG)

# Threads
from threads.MaxwellReadStreamThread import MaxwellReadStreamThread
from threads.MaxwellStimulationThread import MaxwellStimulationThread
from threads.PatternGeneratorThread import PatternGeneratorThread
from threads.ActivityAnalysisThread import ActivityAnalysisThread

class MainWindow():
    """Main application"""
    def __init__(self, app):
        super().__init__()
        self.app = app

        # Read experiment configuration
        fpath_cfg, cfg = load_yaml_configuration_file()
        self.timeout = cfg.get('RUNTIME')
        self.maxwell_params = cfg.get('MAXWELL_PARAMS', {})

        # Initialize Maxwell array
        self_maxwell_el_array, self.maxwell_cfg_el_array = init_maxwell_array(self.maxwell_params['ELEC_ARRAY']['FPATH_CFG'])

        # Initialize threads
        self.maxwell_read_thread = MaxwellReadStreamThread( 
                                    self.maxwell_params['SAMPLE_STREAM']['N_SAMPLES'],
                                    range(self.maxwell_params['SAMPLE_STREAM']['CHANNELS'])
                                   )
        
        self.pattern_gen_thread  = PatternGeneratorThread( 
                                   )
        self.act_analysis_thread = ActivityAnalysisThread(
                                    self.maxwell_read_thread.rx_samples_rdy # pipe signal from read data maxwell
                                   )
        
        self.maxwell_stim_thread = MaxwellStimulationThread( 
                                    self_maxwell_el_array,
                                    self.maxwell_cfg_el_array,
                                    self.pattern_gen_thread.stim_flag_data, # pipe signal from gen pattern
                                    self.maxwell_params['UNIFIED_STIMULATOR']['CHAN_ID'],
                                    self.maxwell_params['UNIFIED_STIMULATOR']['AMP_MV'], 
                                    self.maxwell_params['UNIFIED_STIMULATOR']['FREQ_HZ']
                                   )
        
        # Start experiment
        self.start()

    def dummy_link_sample_stream(self, rx_samples:np.ndarray):
        """Dummy link to Maya thread: samples read from Maxwell"""
        # print(rx_samples)

    def dummy_link_stimulation_source(self):
        """Dummy link to Maya thread: trigger stimulation"""
        pass

    def start(self):
        """Start the experiment"""
        logger.info("Start experiment")

        # Start threads
        self.maxwell_read_thread.start()
        self.maxwell_stim_thread.start()
        self.pattern_gen_thread.start()
        self.act_analysis_thread.start()

        # Start timers
        self.timer_timeout_exp = QTimer.singleShot(self.timeout*1000, self.stop)
    
    def stop(self):
        """Stop the experiment"""
        logger.info("Stop experiment")

        # Stop threads
        self.maxwell_read_thread.stop()
        self.maxwell_stim_thread.stop()
        self.pattern_gen_thread.stop()
        self.act_analysis_thread.stop()

        # Join threads
        self.maxwell_read_thread.wait()
        self.maxwell_stim_thread.wait()
        self.pattern_gen_thread.wait()
        self.act_analysis_thread.wait()

        # Close application
        self.close_qt_app()

    def close_qt_app(self):
        logger.info("Close application")
        sys.exit()


if __name__ == "__main__":
    # Run application
    app = QApplication(sys.argv)
    win = MainWindow(app)
    sys.exit(app.exec())