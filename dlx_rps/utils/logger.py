# -*- coding: utf-8 -*-
# @title      Logger
# @file       load_cfg.py
# @author     Romain Beaubois
# @date       10 Oct 2024
# @copyright
# SPDX-FileCopyrightText: © 2024 Romain Beauboois <refbeaubois@yahoo.com>
# SPDX-License-Identifier: MIT
#
# @brief
# * Wrap logger for debug and module name 
#
# @details

import logging, coloredlogs, sys

def setup_logger(name, debug=False):
    # Set up basic configuration
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            stream=sys.stderr
        )
        coloredlogs.install(level=logging.DEBUG)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            stream=sys.stderr
        )
        coloredlogs.install()

    # Get logger with given name (module name)
    logger = logging.getLogger(name)

    return logger