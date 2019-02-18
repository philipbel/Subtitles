# Copyright (C) 2019 Philip Belemezov.
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

import requests
import shutil
import gzip
import os
import enum

from log import logger
from typing import List, Dict
from functools import partial
from task import Task
from tempfile import NamedTemporaryFile
from os import path
from pathlib import Path
from PyQt5.Qt import (
    pyqtSignal,
    QObject,
    QThreadPool,
    QUrl,
)
from PyQt5.QtGui import (
    QDesktopServices,
)
from abc import ABC

@enum.unique
class Status(enum.IntEnum):
    EMPTY = enum.auto()
    HASHING = enum.auto()
    SEARCHING = enum.auto()
    SUBTITLES_FOUND = enum.auto()
    SUBTITLES_NOT_FOUND = enum.auto()
    DOWNLOADING = enum.auto()
    SUBTITLE_DOWNLOADED = enum.auto()


class SubtitleDownload(QObject):
    onError = pyqtSignal(Exception, Task)
    onStatusChanged = pyqtSignal(Status, float)

    def __init__(self,
                 file_path: Path,
                 language: str = 'eng',
                 threadPool: QThreadPool = QThreadPool.globalInstance(),
                 parent: QObject = None):
        super().__init__(parent)

        self._threadPool = threadPool

        self.file_path = file_path  # TODO: Validate
        self.hash: int = 0
        self.language = language  # TODO: Validate
        self.results: List[Dict[str, str]] = list()
        self.selected_subtitle: Dict[str, str] = dict()
        self.subtitle_filepath: Path = ''

        self._status = SubtitleDownload.State()

    def _onSubtitlesFound(self):
        logger.debug()
        if not self.results:
            logger.debug("No results found")
            self._status = SubtitleDownload.State.SUBTITLES_NOT_FOUND
            self.onStatusChanged.emit(self.tr("Downloading subtitles"), -1)

        self.selected_subtitle = self.results[0]  # TODO: Handle the other subtitles
        self.onStatusChanged.emit(self.tr("Downloading subtitles"), -1)
        self._schedule("Download Subtitles",
                       func=self._downloadSubtitle,
                       onSuccess=self._onSubtitlesDownloaded,
                       onError=self.onError.emit)

    def _downloadFile(self, url: QUrl, outfile: Path):
        pass

    def _downloadSubtitle(self):
        sub: Dict[str, str] = self.selected_subtitle
        url: str = sub['downloadLink']
        logger.debug(f"Downloading subtitle: {url}")
        r = requests.get(url, stream=True)
        self.onStatusChanged.emit(self.tr("Saving file"), -1)
        try:
            prefix = 'SubtitleDownloader'
            tempfile_unzipped = NamedTemporaryFile(prefix=prefix, delete=False)
            with NamedTemporaryFile(prefix=prefix) as tempfile:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, tempfile)
                with gzip.open(tempfile.name) as gz:
                    shutil.copyfileobj(gz, tempfile_unzipped)

            dirname = path.dirname(self.file_path)
            basename = path.splitext(path.basename(self.file_path))[0]
            sub_basename = f"{basename}.{sub['language_id']}.{sub['format']}"
            filename = path.join(dirname, sub_basename)
            logger.debug("filename: {}".format(filename))
            os.rename(tempfile_unzipped.name, filename)

            self.subtitle_filepath = filename
            return
        except Exception as e:
            if tempfile_unzipped:
                os.remove(tempfile_unzipped.name)
            raise e

    def _onSubtitlesDownloaded(self):
        logger.debug(f"Launching video file")
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.file_path))
        # TODO: Convert encoding

    def _findSubtitles(self):
        logger.debug()
        if not self._token:
            logger.debug("Not authenticated, performing login()")
            self._token = self._subService.login()
            if not self._token:
                # TODO: Define exception class
                raise Exception("Unable to login")
        logger.debug(f"_findSubtitles: token={self._token}")
        self.results = self._subService.find_by_hash(self.hash)

    def _onHashCalculated(self):
        logger.debug()
        self._updateStatus(Status.SEARCHING)
        self._schedule("Find Subtitles",
                       func=self._findSubtitles,
                       onSuccess=self._onSubtitlesFound,
                       onError=self.onError.emit)

    def _calculateHash(self):
        self._status = SubtitleDownload.State.HASHING
        self.onStatusChanged.emit(self._status, -1)
        self.hash = self._subService.calculate_hash(self.file_path)

    def __str__(self):
        return f"""SubtitleRequest(
            file_path={self.file_path},
            hash={self.hash},
            language='{self.language}',
            results=[{len(self.results)}],
            url='{self.selected_subtitle.get("downloadLink")}')
        """

    def _updateStatus(self, status: Status, progress: float = -1):
        self._status = status
        self.onStatusChanged.emit(self._status, progress)

    def _rescheduleTask(self, task) -> Task:
        return self._schedule(task.name, task.func, task.onSuccess, task.onError)

    def _schedule(self, name, func, onSuccess, onError=None) -> Task:
        task = Task(func, name, onSuccess, onError)
        self._scheduleTask(task)
        return task

    def _scheduleTask(self, task: Task) -> None:
        logger.debug(f"ThreadPool starting task {task}")
        self._threadPool.start(task)

    def download(self):
        self._schedule("Hash",
                       partial(self._calculateHash),
                       onSuccess=self._onHashCalculated,
                       onError=self.onError.emit)
