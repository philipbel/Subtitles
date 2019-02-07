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

import shutil
import os
import gzip
import sys
import requests
from enum import IntEnum, auto, unique
from os import path
from PyQt5.Qt import (
    pyqtSlot,
    QAction,
    QApplication,
    QByteArray,
    QErrorMessage,
    QKeySequence,
    QMainWindow,
    QMenu,
    QMimeDatabase,
    QMimeType,
    QSizePolicy,
    Qt,
    QThreadPool,
    QUrl,
)
from PyQt5.QtGui import (
    QCloseEvent,
    QDesktopServices,
)
from PyQt5.QtWidgets import (
    QDesktopWidget,
    QFileDialog,
    QLabel,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QStackedLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from .task import Task
from .PreferencesDialog import PreferencesDialog
from .AboutDialog import AboutDialog
from .DndWidget import DndWidget
from .Settings import Settings
from service.OpenSubService import OpenSubService
from service.EncodingService import EncodingService
from log import logger
from functools import partial
from tempfile import NamedTemporaryFile
from typing import List, Dict

PROG = 'Subtitles'


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._subService = OpenSubService()
        self._encService = EncodingService()
        self._token = None

        self._threadPool = QThreadPool.globalInstance()

        self._initUi()

        self._restoreWindowSettings()

    def _initUi(self):
        self._initCentralWidget()

        self._dndWidget = DndWidget(self.centralWidget())
        self._dndWidget.filesDropped.connect(self.processVideoFiles)
        self.centralWidget().layout().addWidget(self._dndWidget)

        self._initMenu()

        self.setWindowTitle(self.tr(PROG))
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.resize(320, 240)  # TODO: Make proportional to the screen size.
        geometry = self.frameGeometry()
        desktopCenter = QDesktopWidget().availableGeometry().center()
        geometry.moveCenter(desktopCenter)
        self.move(geometry.topLeft())

    def _initMenu(self):
        # mb = self.menuBar()
        self.setMenuBar(None)
        mb = QMenuBar(parent=None)
        # self.setMenuBar(mb)

        fileMenu = mb.addMenu(self.tr("&File"))
        openMovieAction = fileMenu.addAction(self.tr("&Open Movie..."))
        openMovieAction.triggered.connect(self.showOpenFile)
        openMovieAction.setShortcut(QKeySequence.Open)

        if sys.platform == 'darwin':
            # XXX: Keep this in the "File" menu.  Qt on macOS will automatically
            # move them to the correct location.
            # Adding them to the QMenuBar directly does not work.
            quitAction = fileMenu.addAction("Quit")
            aboutAction = fileMenu.addAction("About")
            preferencesAction = fileMenu.addAction("preferences")
        else:
            ABOUT_ACTION = "&About"
            if sys.platform == 'win32':
                PREFERENCES_ACTION = self.tr("&Settings")
                QUIT_ACTION = self.tr("Exit")
            else:
                PREFERENCES_ACTION = self.tr("&Preferences")
                QUIT_ACTION = self.tr("Quit")
            editMenu = mb.addMenu(self.tr("&Edit"))
            preferencesAction = editMenu.addAction(PREFERENCES_ACTION)

            quitAction = fileMenu.addAction(QUIT_ACTION)

            helpMenu = mb.addMenu(self.tr("&Help"))
            aboutAction = helpMenu.addAction(ABOUT_ACTION)

        aboutAction.triggered.connect(self.showAbout)
        aboutAction.setMenuRole(QAction.AboutRole)
        preferencesAction.setShortcut(QKeySequence.Preferences)
        preferencesAction.triggered.connect(self.showPreferences)
        preferencesAction.setMenuRole(QAction.PreferencesRole)
        # Work around QTBUG-65245
        quitAction.setShortcut(QKeySequence.Quit)
        quitAction.triggered.connect(QApplication.instance().quit)
        quitAction.setMenuRole(QAction.QuitRole)

        self.setMenuBar(mb)

    def closeEvent(self, event: QCloseEvent):
        self._saveWindowSettings()

    def _saveWindowSettings(self):
        settings = Settings()
        settings.set(Settings.WINDOW_GEOMETRY, self.saveGeometry())
        settings.set(Settings.WINDOW_STATE, self.saveState())

    def _restoreWindowSettings(self):
        settings = Settings()
        geometryValue: QByteArray = settings.get(Settings.WINDOW_GEOMETRY)
        stateValue: QByteArray = settings.get(Settings.WINDOW_STATE)
        try:
            self.restoreGeometry(geometryValue.data())
            self.restoreState(stateValue)
        except Exception as e:
            logger.warn(f"Error restoring window geometry or state: {e}")
            return

    @pyqtSlot()
    def showOpenFile(self):
        dlg = QFileDialog(self)
        dlg.setWindowTitle(self.tr("Open Video Files"))
        dlg.setWindowModality(Qt.WindowModal)

        mimeFilters = [
            "video/mp4",
            "video/quicktime",
            "video/x-msvideo",
            "video/x-ms-wmv"
        ]
        globPatterns = []
        db = QMimeDatabase()
        for m in mimeFilters:
            mimeType = db.mimeTypeForName(m)
            if not mimeType.isValid():
                logger.warn("Invalid MIME type: {}".format(m))
                continue
            globPatterns.extend(mimeType.globPatterns())
        globText = ' '.join(globPatterns)
        logger.debug("Video glob patterns: {}".format(globText))

        dlg.setNameFilters([
            self.tr("Video Files ({})").format(globText),
            self.tr("All Files (*)")
        ])
        dlg.setAcceptMode(QFileDialog.AcceptOpen)
        dlg.setOption(QFileDialog.ReadOnly, True)
        dlg.setOption(QFileDialog.DontUseCustomDirectoryIcons, True)
        dlg.setLabelText(QFileDialog.Accept, self.tr("Open Movie"))
        dlg.setFileMode(QFileDialog.ExistingFiles)

        if dlg.exec_():
            filenames = dlg.selectedFiles()
            self.processVideoFiles(filenames)

    @pyqtSlot()
    def showAbout(self):
        dlg = AboutDialog(self)
        dlg.exec_()

    def _initCentralWidget(self):
        centralWidget = QWidget(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

    @pyqtSlot()
    def showPreferences(self):
        prefDialog = PreferencesDialog(
            subtitleService=self._subService,
            encodingService=self._encService,
            parent=self)
        code = prefDialog.exec_()
        logger.debug("Preference dialog code: {}".format(code))

    def _onSubtitlesFound(self, filePath, subtitles):
        logger.debug(
            "_onSubtitlesFound: filePath={}, subtitles=\n{}".format(filePath,
                                                                    subtitles))
        if not subtitles:
            # TODO: Display a message
            logger.warning("No subtitles found")

        subtitle = subtitles[0]  # TODO: Handle the other subtitles
        self._schedule("Download Subtitles",
                       func=partial(self._downloadSubtitle, subtitle, filePath),
                       onSuccess=partial(self._onSubtitlesDownloaded, filePath),
                       onError=self._errorHandler)

    def _downloadSubtitle(self, subtitleDict: Dict, moviePath: str) -> str:
        url = subtitleDict['downloadLink']
        logger.debug("Downloading subtitle: {}".format(url))
        r = requests.get(url, stream=True)
        try:
            tempfile_unzipped = NamedTemporaryFile(
                prefix=PROG, delete=False)
            with NamedTemporaryFile(prefix=PROG) as tempfile:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, tempfile)
                with gzip.open(tempfile.name) as gz:
                    shutil.copyfileobj(gz, tempfile_unzipped)

            dirname = path.dirname(moviePath)
            basename = path.splitext(path.basename(moviePath))[0]
            sub_basename = "{}.{}.{}".format(
                basename, subtitleDict['language_id'], subtitleDict['format'])
            filename = path.join(dirname, sub_basename)
            logger.debug("filename: {}".format(filename))
            os.rename(tempfile_unzipped.name, filename)
            return filename
        except Exception as e:
            if tempfile_unzipped:
                os.remove(tempfile_unzipped.name)
            raise e

    def _onSubtitlesDownloaded(self, filePath: str, subtitlePath: str):
        logger.debug(f"filePath={filePath}, subtitlePath={subtitlePath}")
        logger.debug(f"Launching video file")
        QDesktopServices.openUrl(QUrl.fromLocalFile(filePath))
        # TODO: Convert encoding

    def _findSubtitles(self, hash: int, filePath: str):
        logger.debug(f"hash={hash}, filePath={filePath}")
        if not self._token:
            logger.debug("Not authenticated, performing login()")
            self._token = self._subService.login()
            if not self._token:
                # TODO: Define exception class
                raise Exception("Unable to login")
        logger.debug(f"_findSubtitles: token={self._token}")
        return self._subService.find_by_hash(hash)

    def _onHashCalculated(self, filePath: str, hash: int, task: Task):
        logger.debug(f"filePath={filePath}, hash={hash}, task={task}")

        self._schedule("Find Subtitles",
                       func=partial(self._findSubtitles, hash, filePath),
                       onSuccess=partial(self._onSubtitlesFound, filePath),
                       onError=self._errorHandler)

    def _saveToken(self, token):
        logger.debug("Got token:{}".format(token))
        self._token = token

    def _rescheduleTask(self, task) -> Task:
        return self._schedule(task.name, task.func, task.onSuccess, task.onError)

    def _schedule(self, name, func, onSuccess, onError=None) -> Task:
        task = Task(func, name, onSuccess, onError)
        self._scheduleTask(task)
        return task

    def _scheduleTask(self, task: Task) -> None:
        logger.debug(f"ThreadPool starting task {task}")
        self._threadPool.start(task)

    def _errorHandler(self, e: Exception, task: Task):
        mb = QMessageBox(self)
        mb.setIcon(QMessageBox.Critical)
        mb.setText(self.tr(f"Error occurred while running '{task.name}''"))
        mb.setInformativeText(self.tr("Would you like to retry?"))
        mb.setDetailedText(str(e) + '\n\n' + str(task))
        mb.addButton(QMessageBox.Close)
        mb.addButton(QMessageBox.Retry)
        mb.setDefaultButton(QMessageBox.Retry)
        # mb.setWindowModality(Qt.WindowModal)
        response = mb.exec_()
        if response == QMessageBox.Retry:
            logger.info(f"Retrying task {task}")
            self._rescheduleTask(task)

    @pyqtSlot('QVariantList')
    def processVideoFiles(self, filePaths: List[str]):
        # TODO: Handle multiple files
        filePath = filePaths[0]
        logger.warn(f"Multiple files not supported, only using the first one: '{filePath}'")
        logger.debug(f"_processFile(): Running worker for filePath '{filePath}'")
        self._schedule("Hash",
                       partial(self._subService.calculate_hash, filePath),
                       onSuccess=partial(self._onHashCalculated, filePath),
                       onError=self._errorHandler)
