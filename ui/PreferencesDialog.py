import sys
from os import path
from PyQt5.Qt import (
    QApplication,
    QIcon,
    QLocale,
    QMimeData,
    Qt,
    QTextCodec,
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QPushButton,
    QVBoxLayout
)
from .Settings import Settings
from Application import Application
from log import logger


class PreferencesDialog(QDialog):
    def __init__(self, subtitleService, encodingService, parent=None):
        super().__init__(parent)

        self._subService = subtitleService
        self._encService = encodingService

        self._initLocales()

        self._initUi()

    def _initLocales(self):
        locales = QLocale.matchingLocales(
            QLocale.AnyLanguage, QLocale.AnyScript, QLocale.AnyCountry)
        localeDict = {}
        for loc in locales:
            langName = QLocale.languageToString(loc.language())
            if langName == "C":
                continue
            if langName in localeDict:
                continue
            localeDict[langName] = loc
        self._localeDict = localeDict

    def _getNativeLanguageName(self, languageName):
        if languageName not in self._localeDict:
            return None
        return self._localeDict[languageName].nativeLanguageName()

    def _initUi(self):
        formLayout = QFormLayout()

        self._langList = self._initLanguageList()
        formLayout.addRow(self.tr("Subtitle languages:"), self._langList)

        self._encodingList = self._initEncodingList()
        formLayout.addRow(self.tr("Save subtitles with encoding:"),
                          self._encodingList)

        # TODO: Make async
        languages = self._subService.get_languages()
        self._onLanguagesReceived(languages)

        browseAppLayout = QHBoxLayout()
        appEdit = QLineEdit(self.tr(""))
        appEdit.setPlaceholderText(self.tr("Default"))
        appEdit.sizePolicy().setHorizontalPolicy(QSizePolicy.Minimum)
        appEdit.sizePolicy().setHorizontalStretch(3)
        browseButton = QPushButton(self.tr("Browse..."))
        browseButton.sizePolicy().setHorizontalStretch(1)
        browseButton.sizePolicy().setHorizontalPolicy(QSizePolicy.Minimum)
        browseAppLayout.addWidget(appEdit)  # TODO:
        browseAppLayout.addWidget(browseButton)
        formLayout.addRow(
            QLabel(self.tr("Use video player:")), browseAppLayout)

        formLayout.addRow(QLabel(),
                          QCheckBox(self.tr(
                              "Automatically play movie after a successful subtitle download.")))

        self.setWindowTitle(self.tr("Preferences"))

        # There are no dialog button on macOS
        self.setWindowModality(Qt.WindowModal)
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(formLayout)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

        self.accepted.connect(self._saveSettings)

    def _initLanguageList(self):
        langList = QListWidget(self)
        langList.addItem(self.tr("Querying languages..."))
        return langList

    def _initEncodingList(self):
        encList = QComboBox(self)

        codecs = QTextCodec.availableCodecs()
        codecNames = sorted([str(x, encoding='ascii')
                             for x in codecs], key=lambda x: x.lower())

        for codec in codecNames:
            encList.addItem(codec)

        preferredCodec = self._getPreferredCodec()
        if preferredCodec not in codecNames:
            preferredCodec = 'UTF-8'
        encList.setCurrentText(preferredCodec)

        return encList

    def _onLanguagesReceived(self, languages):
        loc = QLocale.system()
        sysLang = QLocale.languageToString(loc.language())
        preferredLanguages = self._getPreferredLanguages()
        self._langList.clear()
        firstCheckedItem = None
        for lang in sorted(languages, key=lambda x: x['name']):
            langName = lang['name']
            langCode = lang['code']
            nativeLang = self._getNativeLanguageName(langName)
            text = langName
            isSystemLang = langName == sysLang
            if nativeLang and not isSystemLang:
                text += " (" + nativeLang + ")"
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setData(Qt.UserRole, langCode)
            if (preferredLanguages and langCode in preferredLanguages) \
                    or isSystemLang:
                item.setCheckState(Qt.Checked)
                firstCheckedItem = item
            else:
                item.setCheckState(Qt.Unchecked)
            self._langList.addItem(item)
        self._langList.setMinimumWidth(self._langList.sizeHintForColumn(0))
        if firstCheckedItem:
            self._langList.scrollToItem(firstCheckedItem)

    def _getPreferredCodec(self):
        settings = Settings()
        enc = settings.get(Settings.ENCODING)
        if enc:
            return enc
        return str(QTextCodec.codecForLocale().name(), encoding='ascii')

    def _getPreferredLanguages(self):
        settings = Settings()
        languages = settings.get(Settings.LANGUAGES)
        if not languages:
            languages = []
        return sorted(languages)

    def _saveSettings(self):
        settings = Settings()
        settings.set(Settings.ENCODING, self._encodingList.currentText())

        languages = []
        for i in range(self._langList.count()):
            item = self._langList.item(i)
            if item.checkState() == Qt.Checked:
                languages.append(item.data(Qt.UserRole))
        settings.set(Settings.LANGUAGES, languages)
