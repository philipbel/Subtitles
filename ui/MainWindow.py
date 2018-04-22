import shutil
import os
import requests
import gzip
import ui.worker
from os import path
from PyQt5.Qt import (
    Qt, QThreadPool, QMainWindow, QErrorMessage, pyqtSlot, QAction,
    QApplication, QMimeType, QMimeDatabase
)
from PyQt5.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, QFileDialog
)
from PyQt5.QtSvg import QSvgWidget
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

PROG = 'SubFinder'


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._subService = OpenSubService()
        self._encService = EncodingService()
        self._token = None

        self._threadPool = QThreadPool.globalInstance()

        self._initUi()

    def _initUi(self):
        self._instructionWidget = self._createInstructionWidget()
        self._spinnerWidget = self._createSpinnerWidget()
        self._spinnerWidget.setVisible(False)
        self._initMenu()

        self.setCentralWidget(self._instructionWidget)
        self.setWindowTitle('SubFinder')
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.resize(320, 240)
        self.setAcceptDrops(True)

    def _initMenu(self):
        # self._menuBar = QMenuBar(parent=None)
        # self.setMenuBar(self._menuBar)

        mb = self.menuBar()
        fileMenu = mb.addMenu(self.tr("&File"))
        openMovieAction = fileMenu.addAction(self.tr("&Open Movie..."))
        openMovieAction.triggered.connect(self.showOpenFile)
        openMovieAction.setShortcut(Qt.CTRL | Qt.Key_O)
        fileMenu.addAction(self.tr("about")).triggered.connect(self.showAbout)
        fileMenu.addAction(self.tr("config")).triggered.connect(
            self.showPreferences)
        # Work around QTBUG-65245
        fileMenu.addAction(self.tr("quit")).triggered.connect(
            QApplication.instance().quit)

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
        layout = QVBoxLayout()
        spinner = QSvgWidget(widget)
        spinner.load('./ui/circles.svg')
        spinner.setFixedSize(64, 64)
        layout.addWidget(spinner)
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
        e.acceptProposedAction()

    def dragLeaveEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        e.acceptProposedAction()
        for url in e.mimeData().urls():
            filename = url.toLocalFile()
            self._processFile(filename)

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
