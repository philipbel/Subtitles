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
    pyqtSignal,
    pyqtSlot,
    QColor,
    QPoint,
    QRect,
    Qt,
)
from PyQt5.QtWidgets import (
    QWidget
)
from PyQt5.QtGui import (
    QBrush,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPainterPath,
    QPalette,
    QPen,
)


class DragAnimationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # self.setBackgroundRole(QPalette.Base)
        # self.setAutoFillBackground(True)

        self._mousePos = QPoint()

    @pyqtSlot()
    def startAnimation(self):
        pass

    @pyqtSlot()
    def stopAnimation(self):
        pass

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        self._mousePos = event.pos()

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(QRect(QPoint(0, 0), self.size()), Qt.yellow)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QBrush(Qt.red), 3))
        painter.drawEllipse(QRect(20, 20, 20, 20))
