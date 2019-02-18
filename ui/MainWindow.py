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
from enum import IntEnum, auto, unique
from PyQt5.Qt import (
    pyqtSlot,
    QAction,
    QApplication,
    QByteArray,
    QErrorMessage,
    QFontDatabase,
    QKeySequence,
    QMainWindow,
    QMenu,
    QMimeDatabase,
    QMimeType,
    QSizePolicy,
    Qt,
)
from PyQt5.QtGui import (
    QCloseEvent,
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
from .SubtitleDownloader import SubtitleDownloader
from service.OpenSubService import OpenSubService, SubtitleNotFoundError
from service.EncodingService import EncodingService
from log import logger
from functools import partial


PROG = 'Subtitles'


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._subService = OpenSubService()
        self._encService = EncodingService()
        self._token = None

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

    def _saveToken(self, token):
        logger.debug("Got token:{}".format(token))
        self._token = token

    @pyqtSlot()
    def handleError(self, error: Exception, task: Task):
        logger.debug(f"downloader={downloader}, task({type(task)})={task}")
        shouldRetry = False
        if isinstance(error, SubtitleNotFoundError):
            text = self.tr(f"No subtitles found for movie \"{downloader.file_path}\"")
        else:
            text = self.tr(f"Error while looking for subtitle for movie "
                           f"\"{path.basename(downloader.file_path)}\"")
            shouldRetry = True

        mb = QMessageBox(self)
        mb.setWindowModality(Qt.WindowModal)
        mb.setSizeGripEnabled(True)
        monospaceFont: str = QFontDatabase.systemFont(QFontDatabase.FixedFont).family()
        mb.setStyleSheet(f"""
            QMessageBoxDetailsText QTextEdit {{
                font-weight: normal;
                font-family: "{monospaceFont}";
                font-size: 10pt;
            }}
            QLabel {{
                font-weight: normal;
            }}
            """)
        mb.setIcon(QMessageBox.Critical)
        mb.setText(text)
        mb.setDetailedText(f"Task '{task.name}', error:\n{error}\n\n")
        mb.addButton(QMessageBox.Close)
        if shouldRetry:
            mb.setInformativeText(self.tr("Would you like to retry?"))
            mb.addButton(QMessageBox.Retry)
            mb.setDefaultButton(QMessageBox.Retry)
        # mb.setWindowModality(Qt.WindowModal)
        response = mb.exec_()
        if shouldRetry and response == QMessageBox.Retry:
            logger.info(f"Retrying task {task}")
            self._rescheduleTask(task)

    @pyqtSlot(str, float)
    def changeStatus(self, message: str, status: float):
        logger.info(f"message={message}, status={status:02f}")  # TODO: Show in the UI

    @pyqtSlot('QVariantList')
    def processVideoFiles(self, filePaths: List[str]):
        for filePath in filePaths:
            language = 'eng'  # TODO: Query
            downloader = SubtitleDownloader(filePath=filePath, language=language)
            downloader.onError.connect(self.handleError)
            downloader.onStatusChanged.connect(self.changeStatus)
            downloader.download()
