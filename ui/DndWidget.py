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
    QAnimationGroup,
    QApplication,
    QColor,
    QDateTime,
    QElapsedTimer,
    QEasingCurve,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRect,
    QRectF,
    QObject,
    Qt,
    QTimer,
)
from PyQt5.QtCore import (
    QParallelAnimationGroup,
)
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLinearLayout,
    QGraphicsScene,
    QGraphicsSceneDragDropEvent,
    QGraphicsSceneMouseEvent,
    QGraphicsWidget,
    QGraphicsView,
    QLabel,
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


class GraphicsItemWrapper(QObject):
    def __init__(self,
                 cls,
                 parent: QObject = None):
        super().__init__(parent)
        self.item = cls()


class EllipseItemWrapper(GraphicsItemWrapper):
    def __init__(self, center: QPointF, radius: float, parent=None):
        super().__init__(cls=QGraphicsEllipseItem, parent=parent)

        self._center = center
        self._radius = radius
        self._updateGeometry()

    def _updateGeometry(self):
        c = self._center
        r = self._radius
        topLeft = QPointF(c.x() - r, c.y() - r)
        bottomRight = QPointF(c.x() + r, c.y() + r)
        rect: QRectF = QRectF(topLeft, bottomRight)
        self.item.setRect(rect)

    @pyqtProperty(float)
    def opacity(self) -> float:
        return self.item.opacity()

    @opacity.setter
    def opacity(self, value: float):
        self.item.setOpacity(value)

    @pyqtProperty(float)
    def radius(self) -> float:
        return self._radius

    @radius.setter
    def radius(self, value: float):
        self._radius = value
        self._updateGeometry()


class Scene(QGraphicsScene):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        super().mouseMoveEvent(event)
        logger.debug(f"pos = {(event.pos().x(), event.pos().y())}"
                     f", scenePos = {(event.scenePos().x(), event.scenePos().y())}")

    def dragEnterEvent(self, event: QGraphicsSceneDragDropEvent):
        super().dragEnterEvent(event)
        logger.debug(f"pos: {event.pos()}, scenePos: {event.scenePos()}")

    def dragMoveEvent(self, event: QGraphicsSceneDragDropEvent):
        super().dragMoveEvent(event)
        logger.debug(f"pos: {event.pos()}, scenePos: {event.scenePos()}")

    def dragLeaveEvent(self, event: QGraphicsSceneDragDropEvent):
        super().dragLeaveEvent(event)
        logger.debug(f"pos: {event.pos()}, scenePos: {event.scenePos()}")

    def dropEvent(self, event: QGraphicsSceneDragDropEvent):
        super().dragLeaveEvent(event)
        logger.debug(f"pos: {event.pos()}, scenePos: {event.scenePos()}")


class DndWidget(QGraphicsView):
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

        # self._updateTimer = QTimer(self)
        # self._updateTimer.setInterval(100)  # 10 Hz
        # self._updateTimer.timeout.connect(self.update)

        self._animationLoop = 0
        # self._lastFrameTime = 0
        # self._animationStartTime = 0
        # self._easingCurve = QEasingCurve(QEasingCurve.OutInCubic)

        # DEBUG:
        self.setMouseTracking(True)

        scene = Scene(parent=self)

        font: QFont = QFontDatabase.systemFont(QFontDatabase.GeneralFont)
        font.setPointSize(18)
        self._textItem = scene.addText(self.tr("Drop Files Here"), font)  # TODO: font
        palette: QPalette = QApplication.instance().palette()
        self._textItem.setDefaultTextColor(palette.color(QPalette.Active, QPalette.Dark))

        textItemAnimation = QPropertyAnimation(self._textItem, b'opacity')
        textItemAnimation.setStartValue(1.0)
        textItemAnimation.setEndValue(0.0)
        textItemAnimation.setDuration(2000)

        self._outerCircleItem = EllipseItemWrapper(center=QPointF(50, 50), radius=20)
        scene.addItem(self._outerCircleItem.item)

        # circleOpacityAnimation = QPropertyAnimation(self._outerCircleItem, b'opacity')
        # circleOpacityAnimation.setStartValue(1.0)
        # circleOpacityAnimation.setEndValue(0.0)
        # circleOpacityAnimation.setDuration(1000)

        # circleRadiusAnimation = QPropertyAnimation(self._outerCircleItem, b'radius')
        # circleRadiusAnimation.setStartValue(0.0)
        # circleRadiusAnimation.setEndValue(500)
        # circleRadiusAnimation.setDuration(7000)

        self.animationGroup = QParallelAnimationGroup(self)
        self.animationGroup.addAnimation(textItemAnimation)
        # self.animationGroup.addAnimation(circleRadiusAnimation)
        # self.animationGroup.addAnimation(circleOpacityAnimation)

        self.setScene(scene)

    # XXX: Debugging
    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        if self.animationGroup.state() != QParallelAnimationGroup.Running:
            self.animationGroup.start()
        else:
            self.animationGroup.stop()

    # XXX: Debugging
    # def mouseMoveEvent(self, event: QMouseEvent):
        # super().mouseMoveEvent(event)
        # logger.debug(f"pos: {event.pos()}")
        # self._outerCircleItem.item.setPos(self.mapToScene(event.pos()))

    @pyqtSlot()
    def startAnimation(self):
        # self._updateTimer.start()
        self._animationLoop = 0
        # self._animationStartTime = QDateTime.currentMSecsSinceEpoch()

    @pyqtSlot()
    def stopAnimation(self):
        # self._updateTimer.stop()
        pass

    # def dragEnterEvent(self, e: QDragEnterEvent):
    #     logger.debug(f"format: {e.mimeData().formats()}, hasImage: {e.mimeData().hasImage()}")

    #     ignoreAction = False
    #     if not e.mimeData().hasUrls():
    #         ignoreAction = True
    #     for url in e.mimeData().urls():
    #         if not url.isLocalFile():
    #             ignoreAction = True
    #     if ignoreAction:
    #         e.setDropAction(Qt.IgnoreAction)
    #         e.ignore()
    #     else:
    #         e.setDropAction(Qt.CopyAction)
    #         e.accept()
    #         self._dragInProgress = True
    #         self.startAnimation()

    # def dragMoveEvent(self, e: QDragMoveEvent):
    #     e.setDropAction(Qt.CopyAction)
    #     e.accept()
    #     if not self.hasFocus():
    #         self.update()
    #     self._mousePos = e.pos()
    #     self.startAnimation()

    # def dragLeaveEvent(self, e: QDragLeaveEvent):
    #     if not self._dragInProgress:
    #         super().dragLeaveEvent(e)
    #     e.accept()
    #     logger.debug("")
    #     self.stopAnimation()
    #     self._dragInProgress = False
    #     self.update()

    # def dropEvent(self, e: QDropEvent):
    #     if e.dropAction() != Qt.CopyAction:
    #         e.ignore()
    #     e.acceptProposedAction()
    #     self.stopAnimation()
    #     files = [url.toLocalFile() for url in e.mimeData().urls()]
    #     self._dragInProgress = False
    #     self.update()
    #     self.filesDropped.emit(files)

    # def _drawPulses(self, painter: QPainter):
    #     curTime = QDateTime.currentMSecsSinceEpoch()
    #     if curTime - self._animationStartTime <= DndWidget.ANIMATION_INITIAL_DELAY:
    #         return
    #     p = self._mousePos
    #     s = self.size()
    #     MAX_CIRCLE_RADIUS = max(p.x(),
    #                             s.width() - p.x(),
    #                             p.y(),
    #                             s.height() - p.y())

    #     outerRad = float(curTime - self._lastFrameTime) * (self._animationLoop + 1)
    #     outerRad *= DndWidget.ANIMATION_SPEED
    #     outerRadRatio = float(outerRad) / MAX_CIRCLE_RADIUS
    #     outerRad *= self._easingCurve.valueForProgress(outerRadRatio)

    #     INNER_RADIUS_DIFF = 20

    #     innerRad = outerRad - INNER_RADIUS_DIFF

    #     logger.debug(f"outerRad={outerRad:.2f}, {(outerRadRatio * 100):.2f}%, "
    #                  f"curTime={curTime}, lastFrameTime={self._lastFrameTime}")

    #     painter.setPen(QPen(QBrush(Qt.red), 3))
    #     painter.drawEllipse(p, outerRad, outerRad)

    #     if innerRad > 0:
    #         painter.setPen(QPen(QBrush(Qt.blue), 3))
    #         painter.drawEllipse(QPoint(p.x(), p.y()),
    #                             innerRad,
    #                             innerRad)

    #     if outerRad >= MAX_CIRCLE_RADIUS:
    #         self._animationLoop = 0

    # def _drawText(self, painter: QPainter, text: str):
    #     widgetRect: QRect = self.geometry()
    #     font: QFont = QFontDatabase.systemFont(QFontDatabase.GeneralFont)
    #     font.setPointSize(18)
    #     painter.setFont(font)

    #     textRect: QRect = painter.boundingRect(widgetRect, Qt.AlignCenter, text)
    #     # DEBUG: ...
    #     # painter.setPen(QPen(QBrush(Qt.black), 1))
    #     # painter.drawRect(textRect)

    #     palette: QPalette = QApplication.instance().palette()
    #     painter.setPen(QPen(palette.color(QPalette.Active, QPalette.Dark), 1))
    #     textRect.moveTo(widgetRect.width() / 2 - textRect.width() / 2,
    #                     widgetRect.height() / 2 - textRect.height() / 2)
    #     painter.drawText(textRect, Qt.AlignCenter, text)

    # def paintEvent(self, event: QPaintEvent):
    #     super().paintEvent(event)

    #     painter = QPainter(self)
    #     # painter.fillRect(QRect(QPoint(0, 0), self.size()), Qt.yellow)  # DEBUG: Remove
    #     painter.setRenderHint(QPainter.Antialiasing)

    #     # TODO: Show number of files.
    #     if self._dragInProgress:
    #         self._drawText(painter, self.tr("Drop Movies"))
    #     else:
    #         self._drawText(painter, self.tr("Drag Movies Here"))
    #         return

    #     self._drawPulses(painter)

    #     self._lastFrameTime = QDateTime.currentMSecsSinceEpoch()
    #     self._animationLoop += 1
