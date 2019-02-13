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
