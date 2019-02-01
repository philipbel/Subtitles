#!/usr/bin/env python3
import sys
import signal
import log
from PyQt5.Qt import PYQT_VERSION_STR
from PyQt5.Qt import QSettings
from PyQt5.QtWidgets import QDesktopWidget
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
    geometry = mainWin.frameGeometry()
    desktopCenter = QDesktopWidget().availableGeometry().center()
    geometry.moveCenter(desktopCenter)
    mainWin.move(geometry.topLeft())
    mainWin.show()

    # TODO: For easier testing
    if len(sys.argv) == 2:
        logger.debug(
            "Processing file from command line: '{}'".format(sys.argv[1]))
        mainWin._processFile(sys.argv[1])

    sys.exit(app.exec_())
