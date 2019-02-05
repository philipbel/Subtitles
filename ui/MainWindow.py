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
    QErrorMessage,
    QKeySequence,
    QMainWindow,
    QMenu,
    QMimeDatabase,
    QMimeType,
    QSizePolicy,
    Qt,
    QThreadPool,
)
from PyQt5.QtWidgets import (
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
# from PyQt5.QtSvg import QSvgWidget
from .task import Task
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

    def _initUi(self):
        self._initCentralWidget()
        self._initMenu()

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

    @unique
    class CentralPage(IntEnum):
        HIDDEN = 0
        DRAG_FILES = auto()
        DROP_FILES = auto()
        HASHING = auto()
        SEARCHING = auto()
        DOWNLOADING = auto()
        LAUNCHING = auto()

    def _initCentralWidget(self):
        centralWidget = QWidget(self)
        layout = QVBoxLayout()
        self._stackLayout = QStackedLayout()
        layout.addLayout(self._stackLayout)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

        def createLabel(text: str, parent: QWidget = centralWidget) -> QLabel:
            label = QLabel(parent)
            label.setText(text)
            label.setAlignment(Qt.AlignCenter)
            return label

        def createPageWithProgressBar(text: str) -> QWidget:
            page = QWidget(centralWidget)
            pageLayout = QVBoxLayout()
            page.setLayout(pageLayout)
            label = QLabel(page)
            label.setText(text)
            label.setAlignment(Qt.AlignCenter)
            progress = QProgressBar(page)
            progress.setMinimum(0)
            progress.setMaximum(0)

            pageLayout.setSpacing(0)

            pageLayout.addStretch()
            pageLayout.addWidget(label)
            pageLayout.addWidget(progress)
            pageLayout.addStretch()

            label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            progress.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

            return page

        self._stackLayout.addWidget(QWidget(centralWidget))
        self._stackLayout.addWidget(createLabel(self.tr('Drag movies here')))
        self._stackLayout.addWidget(createLabel(self.tr('Drop the files here')))
        self._stackLayout.addWidget(createPageWithProgressBar(self.tr('Calculating hash...')))
        self._stackLayout.addWidget(createPageWithProgressBar(self.tr('Searching for subtitles...')))
        self._stackLayout.addWidget(createLabel(self.tr('Downloading subtitles...')))
        self._stackLayout.addWidget(createLabel(self.tr('Launching movie')))

        self.setCentralPage(MainWindow.CentralPage.DRAG_FILES)

    @pyqtSlot(int)
    def setCentralPage(self, page: CentralPage):
        self._stackLayout.setCurrentIndex(page.value)

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

    def _processFile(self, filePath):
        logger.debug(f"_processFile(): Running worker for filePath '{filePath}'")
        self._schedule("Hash",
                       partial(self._subService.calculate_hash, filePath),
                       onSuccess=partial(self._onHashCalculated, filePath),
                       onError=self._errorHandler)
