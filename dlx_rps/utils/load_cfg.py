# -*- coding: utf-8 -*-
# @title      Load and parse yaml configuration file
# @file       load_cfg.py
# @author     Romain Beaubois
# @date       10 Oct 2024
# @copyright
# SPDX-FileCopyrightText: © 2024 Romain Beauboois <refbeaubois@yahoo.com>
# SPDX-License-Identifier: MIT
#
# @brief
# * Load yaml configuration file
# 
# @details

# GUI File path
import os, sys
import yaml

## tkinter
import tkinter as tk
from tkinter.filedialog import askopenfilename
tk.Tk().withdraw()

## pyqt5
from PyQt5.QtWidgets import (QFileDialog, QApplication)

# Loger
from config import DEBUG
from utils.logger import setup_logger
logger = setup_logger(__name__, debug=DEBUG)

# ---
# Load configuration file
# ---
def load_yaml_configuration_file():
    """Load experiment configuration file"""
    # Ask configuration file path
    if QApplication.instance(): # if qt app running uses Qt
        fpath_config, _ = QFileDialog.getOpenFileName(
            None,
            "Select a YAML file",
            "",
            "YAML files (*.yaml);;All files (*)"
        )
    else: # is not qt app use tkinter
        fpath_config = askopenfilename(
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")], 
            defaultextension='.yaml'
        )

    # Check path
    if fpath_config:
        if os.path.splitext(fpath_config)[1] == ".yaml":
            logger.info('Load configuration file: %s', fpath_config)
        else:
            logger.error('Wrong configuration file format: %s', fpath_config)
            sys.exit()
    else:
        logger.error('No configuration file specified')
        sys.exit()

    # Extract parameters
    with open(fpath_config, 'r', encoding='utf-8') as file:
        cfg = yaml.safe_load(file)

    return fpath_config, cfg