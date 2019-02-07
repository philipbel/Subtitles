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
from PySide2.QtCore import (
    QRect,
    Qt,
)
from PySide2.QtGui import (
    QFontMetrics,
)
from PySide2.QtWidgets import (
    qApp,
    QDesktopWidget,
    QDialog,
    QDialogButtonBox,
    QTextEdit,
    QVBoxLayout,
)
from log import logger

PHI = 1.61803398875


class TextDialog(QDialog):
    def __init__(self, title, parent=None, html_filename=None, html=None):
        super().__init__(parent)

        self._adjustGeometry()

        self.setWindowTitle(title)

        if html:
            self._html = html
        elif html_filename:
            self._html = TextDialog._loadFileContents(html_filename)
        else:
            raise ValueError('No HTML or HTML file specified')

        layout = QVBoxLayout()
        self.setLayout(layout)

        textWidget = QTextEdit(self)
        textWidget.setHtml(self._html)
        layout.addWidget(textWidget)

        if sys.platform != 'darwin':
            buttonBox = QDialogButtonBox(QDialogButtonBox.Close)
            buttonBox.accepted.connect(self.close)
            buttonBox.rejected.connect(self.close)
            layout.addWidget(buttonBox)

    def _adjustGeometry(self):
        screenRect: QRect = qApp.desktop().screenGeometry()
        myGeometry = self.geometry()
        myGeometry.setHeight(screenRect.height() / PHI)
        myGeometry.setWidth(screenRect.width() / 2.5)
        if self.parent():
            myGeometry.moveCenter(self.parent().geometry().center())
        else:
            myGeometry.moveCenter(screenRect.center())
        self.setGeometry(myGeometry)

    @staticmethod
    def _loadFileContents(filename):
        try:
            with open(filename, 'rb') as f:
                return str(f.read(), encoding='utf-8')
        except Exception as e:
            logger.warn("Error reading from file '{}': {}".format(filename, e))
