import shutil
import os
import gzip
import ui.worker
import sys
import requests
from urllib.parse import urlparse
from os import path
from typing import (
    List
)
import rx
import rx.subjects
import rx.concurrency
import rx.concurrency.mainloopscheduler
import rx.operators as rxops
# TODO: rx.from_ is missing the scheduler parameter.  File a bug.
import rx.core.observable.fromiterable
from PyQt5 import QtCore
from PyQt5.Qt import (
    pyqtSlot,
    QAction,
    QApplication,
    QErrorMessage,
    QKeySequence,
    QMainWindow,
    QMenu,
    QMimeDatabase,
    QMimeType,
    Qt,
    QThreadPool,
    QUrl,
)
from PyQt5.QtWidgets import (
    QFileDialog,
    QLabel,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
# from PyQt5.QtSvg import QSvgWidget
from .worker import Worker
from .PreferencesDialog import PreferencesDialog
from .AboutDialog import AboutDialog
# from pprint import pformat
from service.OpenSubService import OpenSubService
from service.EncodingService import EncodingService
from log import logger
# import multiprocessing
# import rx
from functools import partial
from tempfile import NamedTemporaryFile

PROG = 'Subtitles'


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._subService = OpenSubService()
        self._encService = EncodingService()
        self._token = None

        self._threadPool = QThreadPool.globalInstance()

        self._initUi()

        self._rxScheduler = rx.concurrency.mainloopscheduler.QtScheduler(QtCore)

    def _initUi(self):
        self._instructionWidget = self._createInstructionWidget()
        self._spinnerWidget = self._createSpinnerWidget()
        self._spinnerWidget.setVisible(False)
        self._initMenu()

        self.setCentralWidget(self._instructionWidget)
        self.setWindowTitle(self.tr(PROG))
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.resize(320, 240)
        self.setAcceptDrops(True)

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

            helpMenu = mb.addMenu(self.tr("Help"))
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
            for f in filenames:
                self._processFile(f)

    @pyqtSlot()
    def showAbout(self):
        dlg = AboutDialog(self)
        dlg.exec_()

    def _createSpinnerWidget(self):
        widget = QWidget(self)
        layout = QHBoxLayout()
        progressBar = QProgressBar(widget)
        progressBar.setValue(0)
        progressBar.setMinimum(0)
        progressBar.setMaximum(0)
        # spinner = QSvgWidget(widget)
        # spinner.load('./ui/circles.svg')
        # spinner.setFixedSize(64, 64)
        # layout.addWidget(spinner)
        return widget

    def _createInstructionWidget(self):
        widget = QWidget(self)
        layout = QVBoxLayout()
        widget.setLayout(layout)

        label = QLabel(self.tr('Drop Files Here'), widget)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        return widget

    @pyqtSlot()
    def showPreferences(self):
        prefDialog = PreferencesDialog(
            subtitleService=self._subService,
            encodingService=self._encService,
            parent=self)
        code = prefDialog.exec_()
        logger.debug("Preference dialog code: {}".format(code))

    def dragEnterEvent(self, e):
        logger.debug("mime: {}".format(e.mimeData().formats()))
        if not e.mimeData().hasUrls():
            # e.ignore()
            return
        for url in e.mimeData().urls():
            if not url.isLocalFile():
                # e.ignore()
                return
        e.acceptProposedAction()

    def dragMoveEvent(self, e):
        # TODO: Validate?
        e.acceptProposedAction()

    def dragLeaveEvent(self, e):
        # TODO: Validate?
        e.accept()

    def dropEvent(self, e):
        # TODO: Validate?
        e.acceptProposedAction()

        files = []
        for url in e.mimeData().urls():
            filename = url.toLocalFile()
            # self._processFile(filename)
            files.append(filename)

        if not files:
            # TODO: Reset message
            return

        if len(files) > 1:
            # TODO: Support multiple files?
            QMessageBox.warning(
                self,
                self.tr("Multiple Video Files"),
                self.tr("You have dropped multiple files. This is not supported. "
                        + "Please drag a single movie file into the window."),
                QMessageBox.Ok)
            return

        # def on_next(files: List[str]):
        #     logger.debug(f"on_next() received: '{files}'.")
        #     raise Exception('Dummy')
       
        # def on_completed():
        #     logger.debug(f"on_completed()")

        # def on_error(e: Exception):
        #     logger.error(e)

        # logger.debug(f"_streamVideoFiles sending {files}.")
        # rx.of(files[0]) \
        #     .subscribe_(scheduler=self._rxScheduler,
        #                 on_next=on_next,
        #                 on_completed=on_completed,
        #                 on_error=on_error)

        def hashMovie(filename: str) -> str:
            logger.debug(f"filename = '{filename}'")
            return "deadbeef00c0ffee"

        def searchForHash(hash: str) -> List[str]:
            logger.debug(f"hash={hash}Raising exception")
            # raise Exception('Exception from searchForHash')
            return ['abc.srt']

        def downloadSubtitle(url: str) -> str:
            logger.debug(f"Downloading URL '{url}'")
            to = path.basename(urlparse(url).path)
            raise Exception(f"Downloading {url} to {to}")
            return to

        def downloadErrorHandler(e: Exception):
            logger.debug(f"Handling ")
            resp: int = QMessageBox.critical(
                self,
                self.tr('Download Error'),
                self.tr(f"Download Error:\n{e}"),
                QMessageBox.Retry,
                QMessageBox.Cancel)
            logger.debug(f"Retry? = {resp == QMessageBox.Retry}")
            return rx.empty()

        rx.just(files[0], scheduler=self._rxScheduler) \
            .pipe(
                rxops.map(hashMovie),
                rxops.map(searchForHash),
                # rxops.catch_exception(handler=handler),
                # rxops.observe_on(rx.concurrency.NewThreadScheduler()),
                # rxops.subscribe_on(self._rxScheduler),
                rxops.map(downloadSubtitle),
                # rxops.observe_on(self._rxScheduler),
                rxops.catch_exception(handler=downloadErrorHandler)) \
            .subscribe_(lambda x: logger.debug(f"Subscriber: {x}"),
                        scheduler=self._rxScheduler)

    def _onSubtitlesFound(self, filePath, subtitles):
        logger.debug(
            "_onSubtitlesFound: filePath={}, subtitles=\n{}".format(filePath,
                                                                    subtitles))
        if not subtitles:
            # TODO: Display a message
            logger.warning("No subtitles found")
        self._downloadSubtitle(subtitles[0], filePath)

    def _downloadSubtitle(self, subtitle, moviePath):
        url = subtitle['downloadLink']
        logger.debug("Downloading subtitle: {}".format(url))
        r = requests.get(subtitle['downloadLink'], stream=True)

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
                basename, subtitle['language_id'], subtitle['format'])
            filename = path.join(dirname, sub_basename)
            logger.debug("filename: {}".format(filename))
            os.rename(tempfile_unzipped.name, filename)
        except Exception as e:
            if tempfile_unzipped:
                os.remove(tempfile_unzipped.name)
            raise e

        # TODO: Convert encoding

    def _findSubtitles(self, hash, filePath):
        logger.debug("hash={}, filePath={}".format(hash, filePath))
        if not self._token:
            logger.debug("Not authenticated, performing login()")
            self._token = self._subService.login()
            if not self._token:
                # TODO: Define exception class
                raise Exception("Unable to login")
        logger.debug("_findSubtitles: token={}".format(self._token))
        return self._subService.find_by_hash(hash)

    def _onHashCalculated(self, filePath, hash):
        logger.debug("filePath={}, hash='{}'".format(filePath, hash))

        self._schedule("Find Subtitles",
                       partial(self._onSubtitlesFound, filePath),
                       self._findSubtitles,
                       hash,
                       filePath)

    def _saveToken(self, token):
        logger.debug("Got token:{}".format(token))
        self._token = token

    def _schedule(self, name, onSuccess, func, *args, **kwargs):
        worker = Worker(func, *args, **kwargs)
        worker.on.success.connect(onSuccess)
        worker.on.error.connect(worker.getErrorFunc(name))
        self._threadPool.start(worker)
        return worker

    def _processFile(self, filePath):
        logger.debug(
            "_processFile(): Running worker for filePath '{}'".format(
                filePath
            ))
        self._schedule("Hash",
                       partial(self._onHashCalculated, filePath),
                       self._subService.calculate_hash,
                       filePath)
