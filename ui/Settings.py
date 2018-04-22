from PyQt5.QtCore import QSettings
from log import logger
from os import path


class Settings(object):
    CORE = "core"
    LANGUAGES = CORE + "/languages"
    ENCODING = CORE + "/encoding"

    def __init__(self):
        super().__init__()

        self._settings = QSettings()
        self._settings.setIniCodec('UTF-8')

        logger.debug("Settings file: '{}'".format(self._settings.fileName()))

    def get(self, name):
        return self._settings.value(name)

    def set(self, name, value):
        self._settings.setValue(name, value)
