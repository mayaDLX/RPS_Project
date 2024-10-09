# -*- coding: utf-8 -*-
# @title      MaxwellIO saving
# @file       saving.py
# @author     Atsuhiro Nabeta, Romain Beaubois
# @copyright
# SPDX-FileCopyrightText: ©2023 Atsuhiro Nabeta <atsuhiro.nabeta.lab@gmail.com>
# SPDX-FileCopyrightText: ©2024 Romain Beaubois <beaubois@iis.u-tokyo.ac.jp>
# SPDX-License-Identifier: MIT
#
# @brief
# Functions to recordings of MaxOne through the API
# * recordings spike only or raw
#
# @details
# > **01 Jan 2023** : file creation (AN)
# > **01 Jul 2024** : add file header (RB)

from typing import (
    Optional,
    Protocol,
    runtime_checkable,
)

from maxlab.saving import Saving


@runtime_checkable
class LocalSaving(Protocol):
    """A protocol that abstracts file saving using `maxlab.Saving` and allows
    for interchangeable file saving operations.
    """

    def start(
        self,
        path: str,
    ) -> None:
        """Start file saving.

        Parameters
        ----------
        path : str
            File path for saving.
        """
        ...

    def stop(self) -> None:
        """Stop file saving."""
        ...


class EmptyLocalSaving(LocalSaving):
    """An empty implementation of `LocalSaving`."""

    def start(
        self,
        path: str,
    ) -> None:
        pass

    def stop(self) -> None:
        pass


class MaxWellLocalSaving(LocalSaving):
    """A `LocalSaving` implementation that saves to a file using
    `maxlab.Saving`.
    """

    WELLS = range(1)

    def __init__(self) -> None:
        """Initialize a new instance."""

        super().__init__()
        self._saving: Optional[Saving] = None

    def start(
        self,
        path: str,
    ) -> None:
        self._saving = Saving()
        self._saving.open_directory("")
        self._saving.set_legacy_format(False)
        self._saving.group_delete_all()
        for well in MaxWellLocalSaving.WELLS:
            self._saving.group_define(well, "routed")
        self._saving.start_file(path)
        self._saving.start_recording(MaxWellLocalSaving.WELLS)

    def stop(self) -> None:
        if self._saving is not None:
            self._saving.stop_recording()
            self._saving.stop_file()
            self._saving.group_delete_all()
            self._saving = None
