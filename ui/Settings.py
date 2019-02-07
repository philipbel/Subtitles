# Copyright (C) 2018--2019 Philip Belemezov.
# All Rights Reserved.
#
# This file is part of Subtitles.
#
# Subtitles is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Subtitles is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Subtitles.  If not, see <https://www.gnu.org/licenses/>.

from PyQt5.QtCore import QSettings
from log import logger
from typing import Any


class Settings(object):
    CORE = "core"
    LANGUAGES = CORE + "/languages"
    ENCODING = CORE + "/encoding"
    WINDOW = "window"
    WINDOW_GEOMETRY = WINDOW + "/geometry"
    WINDOW_STATE = WINDOW + "/state"

    def __init__(self):
        super().__init__()

        self._settings = QSettings()
        self._settings.setIniCodec('UTF-8')
        logger.debug("Settings file: '{}'".format(self._settings.fileName()))

    def get(self, name: str) -> Any:
        try:
            value = self._settings.value(name)
        except Exception as e:
            logger.warn(f"Error getting setting '{name}': {e}")
        return value

    def set(self, name: str, value: Any):
        try:
            self._settings.setValue(name, value)
        except Exception as e:
            logger.warn(f"Error setting setting '{name}' to '{value}': {e}")
