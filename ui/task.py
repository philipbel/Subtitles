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

from PyQt5.QtCore import QRunnable, QObject
from PyQt5.Qt import pyqtSlot, pyqtSignal, QErrorMessage
import traceback
from log import logger
from typing import Callable

#
# From https://martinfitzpatrick.name/article/multithreading-pyqt-applications-with-qthreadpool/
#


class TaskSignals(QObject):
    success = pyqtSignal(object, QRunnable)
    error = pyqtSignal(Exception, QRunnable)

    def __init__(self):
        super().__init__()


class Task(QRunnable):
    def __init__(self,
                 func: Callable,
                 name: str,
                 onSuccess: Callable[[object, QRunnable], None],
                 onError: Callable[[Exception, QRunnable], None] = None):
        super().__init__()
        self.func = func
        self.name = name
        self.stop = False
        self.onSuccess = onSuccess
        self.onError = onError
        self._on = TaskSignals()
        self._on.success.connect(onSuccess)
        if onError:
            self._on.error.connect(onError)
        # self.setAutoDelete(False)

    @pyqtSlot()
    def setStop(self):
        self.stop = True

    @pyqtSlot()
    def run(self):
        if self.stop:
            return
        logger.debug("Running")
        try:
            logger.debug(f"Invoking func {self.func}")
            result = self.func()
        except Exception as e:
            logger.error(f"Got exception from func: {e}")
            self._on.error.emit(e, self)
        else:
            logger.debug("func finished")
            try:
                self._on.success.emit(result, self)
            except Exception as e:
                logger.error(f"Success function exception: {e}")
                self._on.error.emit(e, self)
        logger.debug(f"Task '{self.name}' returning")

    def __del__(self):
        logger.debug("")

    def __str__(self):
        return f"Task ('{self.name}', func={self.func}, onSuccess={self.onSuccess}, " \
            f"onError={self.onError}, stop={self.stop})"

    # def getErrorFunc(self, message):
    #     def error_func(error_details):
    #         # TODO: Display the error message to the user
    #         msg = "Error: {}, {}\n{}".format(
    #             message,
    #             error_details.error_message,
    #             error_details.details)
    #         logger.error(msg)
    #         QErrorMessage.qtHandler().showMessage(msg)
    #     return error_func
