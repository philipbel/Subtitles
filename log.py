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

import logging
import sys

logger = logging.getLogger('SubFinder')


def init():
    # TODO: Make configurable
    logger.setLevel(logging.DEBUG)
    # TODO: Create a file handler and log to a file
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s %(levelname)s %(thread)x] "
        "%(filename)s:%(lineno)d:%(funcName)s: %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
