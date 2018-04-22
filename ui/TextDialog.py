import sys
from PyQt5.Qt import Qt, QFontMetrics
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QTextEdit
)
from log import logger


class TextDialog(QDialog):
    def __init__(self, parent=None, filename=None, text=None):
        super().__init__(parent)

        self.setWindowTitle(self.tr("Acknowledgements"))

        self._text = text
        if not self._text and filename:
            self._loadTextFromFile(filename)

        layout = QVBoxLayout()
        self.setLayout(layout)

        textWidget.setHtml(
            '''
            <html>
            <head/>
            <body>
            {}
            </body>
            </html>
            '''.format(self._text))
        layout.addWidget(textWidget)

        if sys.platform != 'darwin':
            buttonBox = QDialogButtonBox(QDialogButtonBox.Close)
            layout.addWidget(button)

    def _loadTextFromFile(self, filename):
        try:
            with open(filename, 'rb') as f:
                self._text = str(f.read(), encoding='utf-8')
        except e:
            logger.warn("Error reading from file '{}': {}".format(filename, e))
