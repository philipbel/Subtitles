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

from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.building.datastruct import TOC

import sys
import re
from string import Template
from os import path

USE_UPX = False

block_cipher = None

# Defaults to .app/Contents/Resources on macOS
RESOURCES_DIR = '.'

with open('doc/VERSION', 'rb') as f:
    VERSION = str(f.read(), encoding='ascii').strip()


def write_subst_file(in_filename, out_filename, subst_dict):
    with open(in_filename, 'rb') as in_file, \
            open(out_filename, 'wb') as out_filename:
        templ = Template(str(in_file.read(), encoding='utf-8'))
        result = templ.safe_substitute(subst_dict)
        out_filename.write(result.encode())

        print("Substitute: {} -> {}".format(in_filename, out_filename))


# From https://github.com/spesmilo/electrum/blob/master/contrib/build-osx/osx.spec
# Workaround for "Retro Look":
binaries = []
for b in collect_dynamic_libs('PySide'):
    if re.match(r'.*style\..*', b[0]):
        print('*** Adding Qt5 Style {}'.format(b[0]))
        binaries.append(b)

data_files = [
    ('doc/VERSION', RESOURCES_DIR),
    ('doc/ACKNOWLEDGEMENTS.html', RESOURCES_DIR),
    # ('doc/LICENSE.PySide', RESOURCES_DIR),
    ('doc/LICENSE.html',  RESOURCES_DIR),
    ('resources/Subtitles.png', RESOURCES_DIR),
]
if path.exists('doc/VERSION.commit'):
    data_files.append(('doc/VERSION.commit', RESOURCES_DIR))
if path.exists('doc/VERSION.build_host'):
    data_files.append(('doc/VERSION.build_host', RESOURCES_DIR))
if path.exists('doc/VERSION.build_number'):
    data_files.append(('doc/VERSION.build_number', RESOURCES_DIR))

a = Analysis(
    [path.join(path.abspath('.'), 'main.py')],
    binaries=binaries,
    datas=data_files,
    hiddenimports=[
        'pythonopensubtitles'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher)

# Required modules
# - DBus
# - PrintSupport
# - Qml
# - Svg
# - Test TODO: Only for testing
# - EglFsKmsSupport?
QT_MODULE_EXCLUDES = [
    'Bluetooth',
    'Designer',
    'Help',
    'Location',
    'Multimedia',
    'MultimediaWidgets',
    'Network',
    'NetworkAuth',
    'Nfc',
    'Positioning',
    'PositioningQuick',
    'Quick',
    'QuickControls2',
    'QuickParticles',
    'QuickTemplates2',
    'Sensors',
    'SerialPort',
    'Sql',
    'WebChannel',
    'WebEngine',
    'WebEngineCore',
    'WebEngineWidgets',
    'WebSockets',
    'XmlPatterns'
]

MODULE_EXCLUDES = []
for x in QT_MODULE_EXCLUDES:
    MODULE_EXCLUDES.extend([prefix + x for prefix in ['Qt', 'Qt5', 'PySide.']])

new_binaries = []

for module, file, typ in a.binaries:
    should_exclude = False
    for qt_mod in MODULE_EXCLUDES:
        if qt_mod in module:
            # print(f"DEBUG: Excluding binary '{module}'")
            should_exclude = True
    if should_exclude:
        continue
    # On Linux, some paths are relative to the qml/ subdirectory, e.g. 
    # .../lib/python3.7/site-packages/PySide/Qt/qml/Qt/labs/platform/../../../../lib/libQt5Widgets.so.5
    # which causes essential Qt libraries to get excluded.
    # So, normalize the path here, and then check for a match.
    file = path.normpath(file)
    if not module.startswith('libpython') and \
        (
            file.startswith('/usr/') or file.startswith('/lib')
            or 'PySide/Qt/qml/' in file
            or module.startswith('PySide/Qt/plugins/sqldrivers')
            or module.startswith('PySide/Qt/plugins/mediaservice')
            or module.startswith('PySide/Qt/plugins/position')
            or module.startswith('PySide/Qt/plugins/sensors')
            or module.startswith('PySide/Qt/plugins/sensorgestures')
            or module.startswith('PySide/Qt/plugins/audio')
            or 'PySide/Qt/plugins/imageformats/libqtga' in module
            or 'PySide/Qt/plugins/imageformats/libqgif' in module
            or 'PySide/Qt/plugins/imageformats/libqicns' in module
            or 'PySide/Qt/plugins/imageformats/libqico' in module
            or 'PySide/Qt/plugins/imageformats/libqwbmp' in module
            or 'PySide/Qt/plugins/imageformats/libqwebp' in module
            or 'PySide/Qt/plugins/imageformats/libqtiff' in module
            or 'PySide/Qt/plugins/platforms/libqeglfs' in module
            or 'PySide/Qt/plugins/platforms/libqlinuxfb' in module
            or 'PySide/Qt/plugins/platforms/libqminimal' in module
            or 'PySide/Qt/plugins/platforms/libqminimalegl' in module
            or 'PySide/Qt/plugins/platforms/libqvnc' in module
            or 'PySide/Qt/plugins/platforms/libqwebgl' in module
            or 'PySide/Qt/plugins/platforms/libqoffscreen' in module
            or 'PySide/Qt/plugins/playlistformats/libqtmultimedia_m3u' in module
            or 'QtWebEngineCore.framework' in file
           ):
        # print(f"Excluding binary '{module}'")
        should_exclude = True
    if should_exclude:
        continue
    new_binaries.append((module, file, typ))


new_datas = []
for module, file, typ in a.datas:
    if module.startswith('PySide/Qt/qml/') \
            or module.startswith('PySide/Qt/lib/QtWebEngineCore.framework') \
            or module.startswith('PySide/Qt/translations') \
            or 'qtwebengine_devtools_resources' in module  \
            or 'qtwebengine_resources' in module \
            or 'QtWebEngineProcess' in module:
        continue
    new_datas.append((module, file, type))


a.binaries = TOC(initlist=new_binaries)
a.datas = TOC(initlist=new_datas)


# for attrib in ['scripts', 'pure', 'binaries', 'datas', 'zipfiles']:
#     fn = attrib + '.txt'
#     with open(fn, 'wb+') as fp:
#         for m, f, t in getattr(a, attrib):
#             fp.write("({}, {}, {})\n".format(m, f, t).encode('utf-8'))
#     print('*** {} written to {}'.format(attrib, fn))


pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Subtitles',
          debug=False,
          strip=True,
          upx=USE_UPX,
          console=False)

if sys.platform == 'win32':
    icon = 'resources/Subtitles.ico'
elif sys.platform == 'darwin':
    icon = 'resources/Subtitles.icns'
else:
    icon = 'resources/Subtitles.png'


coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=USE_UPX,
               name='Subtitles',
               icon=icon)

if sys.platform == 'darwin':
    app = BUNDLE(coll, name='Subtitles.app', icon=icon)
    write_subst_file(
        in_filename='resources/Info.plist.in',
        out_filename=path.join(app.name, 'Contents/Info.plist'),
        subst_dict=dict(
            VERSION=VERSION
        )
    )
