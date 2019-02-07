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

import unittest

from .context import service


TEST_HASH = '92099e543d2a0841'

class OpenSubServiceTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_calculate_hash(self):
        pass

    def test_download_by_hash(self):
        svc = service.OpenSubService()
        svc.download_by_hash(TEST_HASH, lambda x: print(str(x)))
