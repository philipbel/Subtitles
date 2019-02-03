import shutil
import os
import gzip
import ui.worker
import sys
import requests
from typing import Dict
# from statemachine import State, StateMachine
from os import path
from PyQt5.Qt import (
    pyqtSlot,
    QAction,
    QApplication,
    QErrorMessage,
    QEvent,
    QEventTransition,
    QFinalState,
    QKeySequence,
    QMainWindow,
    QMenu,
    QMimeDatabase,
    QMimeType,
    QObject,
    QState,
    QStateMachine,
    Qt,
    QThreadPool,
)
from PyQt5.QtWidgets import (
    QFileDialog,
    QLabel,
    QMenuBar,
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

# class DragDropStateMachine(StateMachine, QOBject):   
#     accepts_files = State(name='Accepts Files', initial=True)
#     files_being_dropped = State(name='Files Being Dropped')
#     files_dropped = State(name='Files Dropped')

#     search_in_progress = State(name='Search in Progress')
#     no_results = State(name='No Results')
#     results_ready = State(name='Results Ready')
    
#     # subtitle_downloading = State(name='Subtitle Downloading')
#     # subtitle_downloaded = State(name='Subtitled Downloaded')
#     # video_launching = State(name='Video Launching')
#     # video_launched = State(name='Video Launched')
#     error = State(name='Error')
#     retry = State(name='Retry')

#     drop_files = accepts_files.to(files_being_dropped)
#     accept_dropped_files = files_being_dropped.to(files_dropped)
#     dismiss_dropped_files = files_being_dropped.to(accepts_files)
    
#     # search_subtitles = files_dropped.to(search_in_progress)
#     # results_ready = search_in_progress.to(results_ready)
#     # results_error = search_in_progress.to(results)



#     def __init__(self, parent=None):
#         super(QObject, self).__init__(parent)


class State(QState):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.data = {}
        
    def onEntry(self, e: QEvent):
        if e.type() == QEvent.StateMachineSignal:
            signalEvent: QStateMachine.SignalEvent = QStateMachine.SignalEvent(e)
            args = signalEvent.arguments()
            if args:
                d = args[0]
                if isinstance(d, dict):
                    self.data = d
WIP



class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._subService = OpenSubService()
        self._encService = EncodingService()
        self._token = None

        self._threadPool = QThreadPool.globalInstance()

        self._initUi()

        self._initStateMachine()

        eventTransition = QEventTransition(self, QEvent.Drop)
        eventTransition.setTargetState(self._stateFilesWereDropped)
        self._stateAcceptsFiles.addTransition(eventTransition)
        self._stateFilesWereDropped.entered.connect(
            lambda: print(f"Dropped"))

        self._sm.start()

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
        self.setMenuBar(None)
        mb = QMenuBar(parent=None)

        fileMenu = mb.addMenu(self.tr("&File"))
        openMovieAction = fileMenu.addAction(self.tr("&Open Movie..."))
        openMovieAction.triggered.connect(self.showOpenFile)
        openMovieAction.setShortcut(QKeySequence.Open)

        if sys.platform == 'darwin':
            # XXX: Keep this in the "File" menu.  Qt on macOS will
            # automatically move them to the correct location.
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

    # def dragEnterEvent(self, e):
    #     logger.debug("mime: {}".format(e.mimeData().formats()))
    #     if not e.mimeData().hasUrls():
    #         # e.ignore()
    #         return
    #     files = []
    #     for url in e.mimeData().urls():
    #         if not url.isLocalFile():
    #             # e.ignore()
    #             return
    #         files.append(url.fileName())
    #     e.acceptProposedAction()

    class DragEnterEventTransition(QEventTransition):
        def __init__(self, parent=None):
            super().__init__(parent=parent)
        
        def eventTest(self, event: QEvent) -> bool:
            if not super().eventTest(event):
                return
            event = QStateMachine.WrappedEvent().event()
            logger.debug("mime: {}".format(event.mimeData().formats()))
            if not event.mimeData().hasUrls():
                # e.ignore()
                return
            files = []
            for url in event.mimeData().urls():
                if not url.isLocalFile():
                    # e.ignore()
                    return
                files.append(url.fileName())
            event.acceptProposedAction()

    def dragMoveEvent(self, e):
        e.acceptProposedAction()

    def dragLeaveEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        logger.debug("dropEvent")
        e.acceptProposedAction()
        for url in e.mimeData().urls():
            filename = url.toLocalFile()
            # self._processFile(filename)  # DEBUG: Disabled

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

    def _createAndAddState(self, name: str = '', final: bool = False) -> QState:
        if final:
            state = QFinalState()
        else:
            state = QState()
        state.setObjectName(name)
        self._sm.addState(state)
        return state

    # states = {
    #     'AcceptsFiles': {
    #         'initial': True,
    #         'to': [

    #         ]
    #     },
    #     'FilesAreBeingDropped': {
    #         'to': [
    #         ]
    #     },
    #     'FilesWereDropped': {
    #         'to': [
    #         ]
    #     },

    #     'SearchIsInProgress': {
    #         'to': [
    #         ]
    #     },
    #     'SearchFoundNoResults': {
    #         'to': [
    #         ]
    #     },
    #     'SearchResultsAreReady': {
    #         'to': [
    #         ]
    #     },
    #     'SearchError': {
    #         'to': [
    #         ]
    #     },
    
    #     'SubtitleIsDownloading': {
    #         'to': [
    #         ]
    #     },
    #     'SubtitleWasDownloaded': {
    #         'to': [
    #         ]
    #     },
    #     'SubtitleDownloadError': {
    #         'to': [
    #         ]
    #     },

    #     'VideoIsLaunching': {
    #         'to': [
    #         ]
    #     },
    #     'VideoWasLaunched': {
    #         'to': [
    #         ]
    #     },
    #     'VideoDownloadError': {
    #         'to': [
    #         ]
    #     },
    # }

    # def _initStates(self,
    #                 stateMachine: QStateMachine,
    #                 states: Dict[str, Dict]):
    #     for name, d in states.items():
    #         state = QState()
    #         state.setObjectName(d[name])
    #         d['object'] = state
    #         setattr(self, 'state' + name, d)
    #         stateMachine.addState(state)
    #     for name, d in states.items():
    #         for to_name in d.get('to', []):
    #             to_state = states[to_name]
    #             if not to_state:
    #                 logger.warn(f"Unable to find state named '{to_name}'")
    #                 return
    #             stateMachine.

    def _initStateMachine(self):
        self._sm = QStateMachine(self)

        # self._initStates()

        # Dragging and dropping files.
        self._stateAcceptsFiles = self._createAndAddState()
        self._stateFilesAreBeingDropped = self._createAndAddState()
        self._stateFilesWereDropped = self._createAndAddState()
        # Subtitle search
        self._stateSearchIsInProgress = self._createAndAddState()
        self._stateSearchError = self._createAndAddState()
        self._stateSearchIsInProgress.setErrorState(self._stateSearchError)
        self._stateSearchFoundNoResults = self._createAndAddState()
        self._stateSearchResultsAreReady = self._createAndAddState()
        # Subtitle download
        self._stateSubtitleIsDownloading = self._createAndAddState()
        self._stateSubtitleWasDownloaded = self._createAndAddState()
        self._stateSubtitleDownloadError = self._createAndAddState()
        # After a subtitle has been downloaded
        self._stateVideoIsLaunching = self._createAndAddState()
        self._stateVideoWasLaunched = self._createAndAddState(final=True)
        self._stateVideoDownloadError = self._createAndAddState()

        self._stateAcceptsFiles.addTransition(self._stateFilesAreBeingDropped)
        self._stateFilesAreBeingDropped.addTransition(self._stateFilesWereDropped)
        self._stateFilesWereDropped.addTransition(self._stateSearchIsInProgress)

        self._sm.setInitialState(self._stateAcceptsFiles)
