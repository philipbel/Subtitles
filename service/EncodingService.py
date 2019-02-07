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

import encodings


class EncodingService(object):
    def __init__(self):
        super().__init__()

        self._encodings = self._get_encodings()

    def _get_encodings(self):
        enc_list = list(set(sorted(encodings.aliases.aliases.values())))
        for i in range(len(enc_list)):
            enc = enc_list[i]
            enc = enc.upper()
            enc = enc.replace('_', '-')
            enc_list[i] = enc
        return sorted(enc_list)

    @property
    def encodings(self):
        return self._encodings
