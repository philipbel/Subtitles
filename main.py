#!/usr/bin/env python3

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

import sys
import signal
import log
from PyQt5.Qt import (
    PYQT_VERSION_STR,
    QSettings,
)
from log import logger
from Application import Application
from ui.MainWindow import MainWindow


signal.signal(signal.SIGINT, signal.SIG_DFL)


if __name__ == "__main__":
    log.init()

    logger.info("Using PyQt5 version {}".format(PYQT_VERSION_STR))

    # Use INI files on Windows, NativeFormat on all other OS
    if sys.platform == 'win32':
        QSettings.setDefaultFormat(QSettings.IniFormat)

    app = Application(sys.argv)
    mainWin = MainWindow()
    mainWin.show()

    # TODO: For easier testing
    if len(sys.argv) == 2:
        logger.debug(
            "Processing file from command line: '{}'".format(sys.argv[1]))
        mainWin.processVideoFile(sys.argv[1])

    sys.exit(app.exec_())
