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

import re
import sys
from typing import List, Tuple
from PyQt5.Qt import (
    PYQT_VERSION_STR,
    pyqtSlot,
    # QDesktopServices,
    QFrame,
    QIcon,
    QSizePolicy,
    Qt,
    # QUrl,
)
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)
from Application import Application
from .TextDialog import TextDialog
# from os import path
from log import logger


class AboutDialog(QDialog):
    LICENSE_FILE_RE = re.compile('<!-- License:\s*(.*) -->')
    RESOURCE_VERSION = 'VERSION'

    def __init__(self, parent=None):
        super().__init__(parent)

        self._initUi()

        self.setFixedSize(self.sizeHint())
        flags = self.windowFlags()
        flags = flags | Qt.CustomizeWindowHint
        flags = flags & ~(Qt.WindowMaximizeButtonHint)
        self.setWindowFlags(flags)

    def _initUi(self):

        app = Application.instance()

        icon = QIcon(app.findResource('Subtitles.png'))

        iconLabel = QLabel()
        iconLabel.setPixmap(icon.pixmap(128))
        iconLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        appNameLabel = QLabel(self)
        appNameLabel.setText(app.applicationName())
        appNameLabel.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        appNameLabel.setStyleSheet('font-weight: bold; font-size: 18pt')
        appNameLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        version_labels = self._createVersionLabels()

        licenseLabel = self._createSelectableLabel(
            'Copyright © 2018–2019 Philip Belemezov<br>'
            'Licensed under the <a href="about:blank">'
            'GNU General Public License, version 3</a>.')
        licenseLabel.setStyleSheet('color: gray; font-size: 8pt')
        licenseLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        licenseLabel.setTextFormat(Qt.RichText)
        licenseLabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
        licenseLabel.linkActivated.connect(self.showLicense)

        homepageLabel = self._createLinkLabel(
            text=self.tr("Homepage"),
            href="https://github.io/philipbel/subtitles")
        homepageLabel.setAlignment(Qt.AlignCenter)

        ackLabel = self._createLinkLabel(text=self.tr("Acknowledgements"))
        ackLabel.setAlignment(Qt.AlignCenter)
        ackLabel.linkActivated.connect(self.showAcknowledgements)

        linksLayout = QVBoxLayout()
        linksLayout.addWidget(homepageLabel)
        linksLayout.addSpacing(5)
        linksLayout.addWidget(ackLabel)

        versionInfoLayout = QFormLayout()
        versionInfoLayout.setFormAlignment(Qt.AlignHCenter)
        versionInfoLayout.setHorizontalSpacing(4)
        for name, value in version_labels:
            name.setText(name.text() + ':')
            versionInfoLayout.addRow(name, value)


        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(0)
        mainLayout.addWidget(iconLabel)
        mainLayout.addWidget(appNameLabel)
        mainLayout.addSpacing(5)
        mainLayout.addLayout(versionInfoLayout)
        mainLayout.addSpacing(20)
        mainLayout.addLayout(linksLayout)
        mainLayout.addSpacing(20)
        mainLayout.addWidget(licenseLabel)

        if sys.platform != 'darwin':
            buttonBox = QDialogButtonBox(QDialogButtonBox.Close)
            buttonBox.setCenterButtons(True)
            buttonBox.button(QDialogButtonBox.Close).clicked.connect(
                self.reject
            )

            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)

            mainLayout.addSpacing(8)
            mainLayout.addWidget(line)
            mainLayout.addSpacing(8)
            mainLayout.addWidget(buttonBox)

    def _createLinkLabel(self, text: str, href: str = None) -> QLabel:
        linkLabel = QLabel()
        # linkLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        linkLabel.setTextFormat(Qt.RichText)
        linkLabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
        if href:
            linkLabel.setText(f'<a href="{href}">{text}</a>')
            linkLabel.setOpenExternalLinks(True)
        else:
            linkLabel.setText(f'<a href="about:blank">{text}</a>')

        return linkLabel

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

    _VERSION_LABELS = [
        {'label': Application.translate(
            'AboutDialog', 'Version'), 'file': 'VERSION'},
        {'label': Application.translate('AboutDialog', 'PyQt Version'),
         'value': PYQT_VERSION_STR},
        {'label': Application.translate('AboutDialog', 'Git Commit'),
         'file': 'VERSION.commit'},
        {'label': Application.translate('AboutDialog', 'Build Number'),
         'file': 'VERSION.build_number'},
        {'label': Application.translate('AboutDialog', 'Build Host'),
         'file': 'VERSION.build_host'},
    ]

    def _createVersionLabels(self) -> List[Tuple[QWidget, QWidget]]:
        version_labels = []

        # my_layout = QFormLayout(self)
        for d in AboutDialog._VERSION_LABELS:
            label_text = d['label']
            if 'value' in d:
                value = d['value']
            else:
                if 'file' not in d:
                    logger.warn(
                        f"No value or file for version label {label_text}")
                    continue
                value = AboutDialog._readFile(d['file'])
                if not value:
                    continue
            versionLabel = QLabel(label_text)
            versionLabel.setStyleSheet("font-size: 10pt")
            versionLabel.setSizePolicy(
                QSizePolicy.Maximum, QSizePolicy.Maximum)
            versionValueLabel = self._createSelectableLabel(value)
            versionValueLabel.setSizePolicy(QSizePolicy.Maximum,
                                            QSizePolicy.Maximum)
            versionValueLabel.setStyleSheet("font-size: 10pt")
            version_labels.append((versionLabel, versionValueLabel))
        return version_labels
