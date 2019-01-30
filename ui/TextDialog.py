import sys
from PyQt5.Qt import (
    Qt,
    QFontMetrics,
    QRect,
)
from PyQt5.QtWidgets import (
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
