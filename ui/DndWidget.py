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

from PyQt5.Qt import (
    pyqtProperty,
    pyqtSignal,
    pyqtSlot,
    QApplication,
    QColor,
    QDateTime,
    QElapsedTimer,
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    Qt,
    QTimer,
)
from PyQt5.QtWidgets import (
    QWidget
)
from PyQt5.QtGui import (
    QBrush,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QFont,
    QFontDatabase,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPainterPath,
    QPalette,
    QPen,
    QStaticText,
)
from log import logger


class DndWidget(QWidget):
    ANIMATION_SPEED = (1.0 / 8)
    ANIMATION_INITIAL_DELAY = 200  # ms

    filesDropped = pyqtSignal('QVariantList')

    def __init__(self, parent=None):
        super().__init__(parent)

        # self.setBackgroundRole(QPalette.Base)
        # self.setAutoFillBackground(True)

        self._mousePos = QPoint()
        self.setAcceptDrops(True)
        self._dragInProgress = False

        self._updateTimer = QTimer(self)
        self._updateTimer.setInterval(100)  # 10 Hz
        self._updateTimer.timeout.connect(self.update)

        self._animationLoop = 0
        self._lastFrameTime = 0
        self._animationStartTime = 0
        self._easingCurve = QEasingCurve(QEasingCurve.OutInCubic)

    @pyqtSlot()
    def startAnimation(self):
        self._updateTimer.start()
        self._animationLoop = 0
        self._animationStartTime = QDateTime.currentMSecsSinceEpoch()

    @pyqtSlot()
    def stopAnimation(self):
        self._updateTimer.stop()

    def dragEnterEvent(self, e: QDragEnterEvent):
        logger.debug(f"format: {e.mimeData().formats()}, hasImage: {e.mimeData().hasImage()}")

        ignoreAction = False
        if not e.mimeData().hasUrls():
            ignoreAction = True
        for url in e.mimeData().urls():
            if not url.isLocalFile():
                ignoreAction = True
        if ignoreAction:
            e.setDropAction(Qt.IgnoreAction)
            e.ignore()
        else:
            e.setDropAction(Qt.CopyAction)
            e.accept()
            self._dragInProgress = True
            self.startAnimation()

    def dragMoveEvent(self, e: QDragMoveEvent):
        e.setDropAction(Qt.CopyAction)
        e.accept()
        if not self.hasFocus():
            self.update()
        self._mousePos = e.pos()
        self.startAnimation()

    def dragLeaveEvent(self, e: QDragLeaveEvent):
        if not self._dragInProgress:
            super().dragLeaveEvent(e)
        e.accept()
        logger.debug("")
        self.stopAnimation()
        self._dragInProgress = False
        self.update()

    def dropEvent(self, e: QDropEvent):
        if e.dropAction() != Qt.CopyAction:
            e.ignore()
        e.acceptProposedAction()
        self.stopAnimation()
        files = [url.toLocalFile() for url in e.mimeData().urls()]
        self._dragInProgress = False
        self.update()
        self.filesDropped.emit(files)

    def _drawPulses(self, painter: QPainter):
        curTime = QDateTime.currentMSecsSinceEpoch()
        if curTime - self._animationStartTime <= DndWidget.ANIMATION_INITIAL_DELAY:
            return
        p = self._mousePos
        s = self.size()
        MAX_CIRCLE_RADIUS = max(p.x(),
                                s.width() - p.x(),
                                p.y(),
                                s.height() - p.y())

        outerRad = float(curTime - self._lastFrameTime) * (self._animationLoop + 1)
        outerRad *= DndWidget.ANIMATION_SPEED
        outerRadRatio = float(outerRad) / MAX_CIRCLE_RADIUS
        outerRad *= self._easingCurve.valueForProgress(outerRadRatio)

        INNER_RADIUS_DIFF = 20

        innerRad = outerRad - INNER_RADIUS_DIFF

        logger.debug(f"outerRad={outerRad:.2f}, {(outerRadRatio * 100):.2f}%, "
                     f"curTime={curTime}, lastFrameTime={self._lastFrameTime}")

        painter.setPen(QPen(QBrush(Qt.red), 3))
        painter.drawEllipse(p, outerRad, outerRad)

        if innerRad > 0:
            painter.setPen(QPen(QBrush(Qt.blue), 3))
            painter.drawEllipse(QPoint(p.x(), p.y()),
                                innerRad,
                                innerRad)

        if outerRad >= MAX_CIRCLE_RADIUS:
            self._animationLoop = 0

    def _drawText(self, painter: QPainter, text: str):
        widgetRect: QRect = self.geometry()
        font: QFont = QFontDatabase.systemFont(QFontDatabase.GeneralFont)
        font.setPointSize(18)
        painter.setFont(font)

        textRect: QRect = painter.boundingRect(widgetRect, Qt.AlignCenter, text)
        # DEBUG: ...
        # painter.setPen(QPen(QBrush(Qt.black), 1))
        # painter.drawRect(textRect)

        palette: QPalette = QApplication.instance().palette()
        painter.setPen(QPen(palette.color(QPalette.Active, QPalette.Dark), 1))
        textRect.moveTo(widgetRect.width() / 2 - textRect.width() / 2,
                        widgetRect.height() / 2 - textRect.height() / 2)
        painter.drawText(textRect, Qt.AlignCenter, text)

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)

        painter = QPainter(self)
        # painter.fillRect(QRect(QPoint(0, 0), self.size()), Qt.yellow)  # DEBUG: Remove
        painter.setRenderHint(QPainter.Antialiasing)

        # TODO: Show number of files.
        if self._dragInProgress:
            self._drawText(painter, self.tr("Drop Movies"))
        else:
            self._drawText(painter, self.tr("Drag Movies Here"))
            return

        self._drawPulses(painter)

        self._lastFrameTime = QDateTime.currentMSecsSinceEpoch()
        self._animationLoop += 1
