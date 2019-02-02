# -*- mode: python -*-

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
for b in collect_dynamic_libs('PyQt5'):
    if re.match(r'.*style\..*', b[0]):
        print('*** Adding Qt5 Style {}'.format(b[0]))
        binaries.append(b)

data_files = [
    ('doc/VERSION', RESOURCES_DIR),
    ('doc/ACKNOWLEDGEMENTS.html', RESOURCES_DIR),
    # ('doc/LICENSE.PyQt5', RESOURCES_DIR),
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
    excludes=[
        # 'PyQt5.QtBluetooth',
        # 'PyQt5.QtWebEngineCore',
        # 'PyQt5.QtWebEngine',
        # 'PyQt5.QtWebEngineWidgets',
        # 'PyQt5.QtLocation',
        # 'PyQt5.QtWebChannel',
        # 'PyQt5.QtQuick',
        # 'PyQt5.QtQuickWidgets',
        # 'PyQt5.QtSql',
        # 'PyQt5.QtWebSockets',
        # 'PyQt5.QtMultimedia',
        # 'PyQt5.QtMultimediaWidgets',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher)


QT_MODULE_EXCLUDES = [
    'QtBluetooth',
    # 'QtDBus',  # Needed by libqcocoa.dylib
    'QtDesigner',
    'QtHelp',
    'QtLocation',
    'QtMultimedia',
    'QtMultimediaWidgets',
    'QtNetwork',
    'QtNetworkAuth',
    'QtNfc',
    'QtPositioning',
    'QtPositioningQuick',
    # 'QtPrintSupport',  # Needed  by libqcocoa.dylib
    'QtQml',
    'QtQuick',
    'QtQuickControls2',
    'QtQuickParticles',
    'QtQuickTemplates2',
    'QtSensors',
    'QtSerialPort',
    'QtSql',
    'QtSvg',
    'QtTest',
    'QtWebChannel',
    'QtWebEngine',
    'QtWebEngineCore',
    'QtWebEngineWidgets',
    'QtWebSockets',
    'QtXmlPatterns'
]

MODULE_EXCLUDES = []
for x in QT_MODULE_EXCLUDES:
    MODULE_EXCLUDES.append(x)
    MODULE_EXCLUDES.append('PyQt5.' + x)

new_binaries = []

for module, file, typ in a.binaries:
    should_exclude = False
    for qt_mod in MODULE_EXCLUDES:
        if qt_mod in module:
            should_exclude = True
    if 'PyQt5/Qt/qml/' in file \
            or 'libqwebgl.dylib' in module \
            or 'libqwebp.dylib' in module \
            or 'libqtiff.dylib' in module \
            or 'libqsvgicon.dylib' in module \
            or module.startswith('PyQt5/Qt/plugins/sqldrivers') \
            or module.startswith('PyQt5/Qt/plugins/mediaservice') \
            or module.startswith('PyQt5/Qt/plugins/position') \
            or module.startswith('PyQt5/Qt/plugins/sensors') \
            or module.startswith('PyQt5/Qt/plugins/sensorgestures') \
            or module.startswith('PyQt5/Qt/plugins/audio') \
            or 'QtWebEngineCore.framework' in file:
        should_exclude = True
    if should_exclude:
        continue
    new_binaries.append((module, file, typ))


new_datas = []
for module, file, typ in a.datas:
    if module.startswith('PyQt5/Qt/qml/') \
            or module.startswith('PyQt5/Qt/lib/QtWebEngineCore.framework') \
            or module.startswith('PyQt5/Qt/translations'):
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
