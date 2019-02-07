import sys
from os import path
from enum import Enum
from PyQt5.Qt import (
    QApplication, QStandardPaths, QSettings
)
from log import logger


class Application(QApplication):
    class ResourceType(Enum):
        IMAGE = 1
        TEXT = 2

    _resourceMap = {
        ResourceType.IMAGE: {
            'extensions': ['.png'],
        }
    }

    def __init__(self, args):
        super().__init__(args)

        # self.setOrganizationName("philipbel")
        self.setOrganizationDomain("philipbel.github.io")
        self.setApplicationName("Subtitles")

        if sys.platform == 'win32':
            QSettings.setDefaultFormat(QSettings.IniFormat)

        self._resourcePaths = self._initResourcePaths()

    def _initResourcePaths(self):
        resourcePaths = []
        resourcePaths.append(path.dirname(__file__))

        resourcePaths.extend(QStandardPaths.standardLocations(
            QStandardPaths.AppLocalDataLocation))

        # For when we're running from the dev tree
        resourcePaths.append(path.abspath(path.curdir))
        resourcePaths.append(path.join(path.abspath(path.curdir), 'resources'))
        resourcePaths.append(path.join(path.abspath(path.curdir), 'doc'))

        return resourcePaths

    def findResource(self, resource, resourceType=None):
        if resourceType:
            extensions = Application._resourceMap[resourceType]['extensions']
        else:
            extensions = ['']
        for p in self._resourcePaths:
            for ext in extensions:
                resourcePath = path.join(p, resource + ext)
                if path.exists(resourcePath):
                    return resourcePath
        logger.warn("Unable to locate resource '{}' of type '{}'".format(
            resource, resourceType
        ))
        return None

    @staticmethod
    def instance():
        assert(isinstance(QApplication.instance(), Application))
        return QApplication.instance()
