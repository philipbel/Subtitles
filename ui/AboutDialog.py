import re
import sys
from PyQt5.Qt import (
    Qt, QIcon, PYQT_VERSION_STR, pyqtSlot, QDesktopServices, QUrl,
    QFrame, QSizePolicy
)
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QDialogButtonBox
)
from Application import Application
from .TextDialog import TextDialog
from os import path
from log import logger


class AboutDialog(QDialog):
    LICENSE_FILE_RE = re.compile('<!-- License:\s*(.*) -->')

    def __init__(self, parent=None):
        super().__init__(parent)

        self._initUi()

    def _initUi(self):
        app = Application.instance()

        icon = QIcon(app.findResource('Subtitles.png'))

        iconLabel = QLabel()
        iconLabel.setPixmap(icon.pixmap(64))
        iconLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        appNameLabel = self._createSelectableLabel(app.applicationName())
        appNameLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        appNameLabel.setStyleSheet('font-weight: bold; font-size: 18pt')

        versionLabel = self._createVersionLabel()

        licenseLabel = self._createSelectableLabel(
            '''Copyright © 2018–2019 Philip Belemezov
            Licensed under the GNU General Public License, version 3''')
        licenseLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        linkLabel = QLabel(parent=self)
        linkLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        linkLabel.setText(
            '<a href="https://github.io/philipbel/subtitles">https://github.io/philipbel/subtitles</a>')
        linkLabel.setTextFormat(Qt.RichText)
        linkLabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
        linkLabel.setOpenExternalLinks(True)

        ackButton = QPushButton('Acknowledgements...')
        ackButton.setDefault(False)
        ackButton.setAutoDefault(False)
        ackButton.clicked.connect(self.showAcknowledgements)

        licenseButton = QPushButton('License...')
        licenseButton.setDefault(False)
        licenseButton.setAutoDefault(False)
        licenseButton.clicked.connect(self.showLicense)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(ackButton)
        buttonLayout.addWidget(licenseButton)
        buttonLayout.addStretch()

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(iconLabel)
        layout.addWidget(appNameLabel)
        layout.addWidget(versionLabel)
        layout.addWidget(licenseLabel)
        layout.addWidget(linkLabel)
        layout.addSpacing(10)
        layout.addLayout(buttonLayout)

        if sys.platform != 'darwin':
            buttonBox = QDialogButtonBox(QDialogButtonBox.Close)
            buttonBox.button(QDialogButtonBox.Close).clicked.connect(
                self.reject
            )

            line = QFrame()
            # line.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)

            layout.addSpacing(8)
            layout.addWidget(line)
            layout.addSpacing(8)
            layout.addWidget(buttonBox)

    def _createSelectableLabel(self, text):
        label = QLabel(parent=self)
        label.setText(text)
        label.setTextInteractionFlags(
            Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse)
        return label

    @pyqtSlot()
    def showAcknowledgements(self):
        app = Application.instance()
        ackFilename = app.findResource('ACKNOWLEDGEMENTS.html')
        if not ackFilename:
            return
        # QDesktopServices.openUrl(QUrl.fromLocalFile(ackFilename))
        textDialog = TextDialog(parent=self,
                                title=self.tr("Acknowledgements"),
                                html_filename=ackFilename)
        textDialog.exec_()

    @pyqtSlot()
    def showLicense(self):
        app = Application.instance()
        licenseFilename = app.findResource('LICENSE.html')
        if not licenseFilename:
            return
        # QDesktopServices.openUrl(QUrl.fromLocalFile(licenseFilename))
        textDialog = TextDialog(parent=self,
                                title=self.tr('Subtitles License'),
                                html_filename=licenseFilename)
        textDialog.exec_()

    @staticmethod
    def _readFile(filename):
        app = Application.instance()

        if not filename:
            return None
        filename = app.findResource(filename)
        if not filename:
            return None

        try:
            with open(filename, 'rb') as f:
                return str(f.read(), encoding='utf-8').strip()
        except e:
            logger.warn(
                "Error reading file '{}': {}".format(filename, e))
        return None

    def _createVersionLabel(self):
        app = Application.instance()
        version = AboutDialog._readFile('VERSION')
        versionLabel = self._createSelectableLabel(
            'Version: {}, PyQt5 Version: {}'.format(version, PYQT_VERSION_STR))
        versionLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        return versionLabel
