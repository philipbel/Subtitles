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

        appNameLabel = self._createSelectableLabel(app.applicationName())
        appNameLabel.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        appNameLabel.setStyleSheet('font-weight: bold; font-size: 18pt')
        appNameLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        version_labels = self._createVersionLabels()

        licenseLabel = self._createSelectableLabel(
            '''Copyright © 2018–2019 Philip Belemezov
            Licensed under the GNU General Public License, version 3 ''')
        licenseLabel.setStyleSheet('color: gray; font-size: 8pt')
        licenseLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        homepageLabel = self._createLinkLabel(
            text=self.tr("Homepage"),
            href="https://github.io/philipbel/subtitles")

        ackLabel = self._createLinkLabel(
            text=self.tr("Acknowledgements"))
        ackLabel.linkActivated.connect(self.showAcknowledgements)

        licenseLinkLabel = self._createLinkLabel(text=self.tr("License"))
        licenseLinkLabel.linkActivated.connect(self.showLicense)

        linksLayout = QHBoxLayout()
        linksLayout.addWidget(homepageLabel)
        linksLayout.addWidget(ackLabel)
        linksLayout.addWidget(licenseLinkLabel)

        leftLayout = QHBoxLayout()
        leftLayout.setAlignment(Qt.AlignTop)
        leftLayout.addWidget(iconLabel)

        rightLayout = QVBoxLayout()
        rightLayout.setSpacing(0)

        rightLayout.addWidget(appNameLabel)

        versionInfoLayout = QGridLayout()
        versionInfoLayout.setHorizontalSpacing(5)
        versionInfoLayout.setVerticalSpacing(0)
        row = 0
        for name, value in version_labels:
            name.setStyleSheet("background-color: red")
            value.setStyleSheet("background-color: green")
            name.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            value.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            name.setText(name.text() + ':')
            versionInfoLayout.addWidget(name, row, 0, Qt.AlignRight)
            versionInfoLayout.addWidget(value, row, 1, Qt.AlignLeft)
            row += 1
        rightLayout.addLayout(versionInfoLayout)

        centralLayout = QHBoxLayout()
        centralLayout.addLayout(leftLayout)
        centralLayout.addLayout(rightLayout)

        mainLayout = QVBoxLayout(self)
        mainLayout.addLayout(centralLayout)
        mainLayout.addLayout(linksLayout)
        mainLayout.addWidget(licenseLabel)

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

    # def _ge(self, resource):
    #     value = AboutDialog._readFile(resource)
    #     return self._createSelectableLabel(value)

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
            # versionLabel.sizePolicy().setVerticalPolicy(QSizePolicy.Maximum)
            versionValueLabel = self._createSelectableLabel(value)
            # versionValueLabel.sizePolicy().setVerticalPolicy(
            #     QSizePolicy.Maximum)
            version_labels.append((versionLabel, versionValueLabel))
        return version_labels
