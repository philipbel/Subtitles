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
from os import path
from enum import Enum
from PySide2.QtCore import (
    QStandardPaths, QSettings
)
from PySide2.QtWidgets import (
    QApplication
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
