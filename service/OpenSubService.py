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

from pythonopensubtitles.utils import File
from pythonopensubtitles import opensubtitles
from log import logger


class OpenSubService(object):
    def __init__(self):
        super().__init__()
        # settings.Settings.VERBOSE = True

        # TODO: Request a proper useragent from
        # http://trac.opensubtitles.org/projects/opensubtitles/wiki/DevReadFirst
        self._ost = opensubtitles.OpenSubtitles(
            user_agent='TemporaryUserAgent')

    def login(self, username='', password=''):
        logger.debug("")
        token = self._ost.login(username=username, password=password)
        logger.debug("Login token: {}".format(token))
        return token

    def calculate_hash(self, filePath):
        logger.debug("filePath: {}".format(filePath))
        f = File(filePath)
        hash = f.get_hash()
        logger.debug("hash: {}".format(hash))
        return hash

    def find_by_hash(self, hash):
        logger.debug("hash={}".format(hash))
        if not hash:
            raise ValueError('hash is empty')
        config = {
            # TODO: Adjust for language
            'sublanguageid': 'eng',
            'moviehash': hash,
            # 'moviebytesize': f.size
        }

        logger.debug("Calling search_subtitles()")
        data = self._ost.search_subtitles([config])
        if not data:
            raise Exception("No data")
            return

        result = []
        logger.debug("Generating subtitles")
        for sub in sorted(data, key=lambda x: x['Score'], reverse=True):
            result.append(dict(size=sub['SubSize'],
                               hash=sub['SubHash'],
                               bad=sub['SubBad'] != '0',
                               rating=sub['SubRating'],
                               downloads=sub['SubDownloadsCnt'],
                               fps=sub['MovieFPS'],
                               featured=sub['SubFeatured'],
                               encoding=sub['SubEncoding'],
                               downloadLink=sub['SubDownloadLink'],
                               language_id=sub['SubLanguageID'],
                               format=sub['SubFormat'],
                               language_id_iso=sub['ISO639']
                               ))
        return result

    def get_languages(self):
        data = self._ost.get_subtitle_languages()
        result = []
        for i in data:
            lang = dict(code=i['ISO639'],
                        name=i['LanguageName'],
                        id=i['SubLanguageID'])
            result.append(lang)
        return result
