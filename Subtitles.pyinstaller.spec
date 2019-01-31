# -*- mode: python -*-

from PyInstaller.utils.hooks import collect_dynamic_libs

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

a = Analysis([
    path.join(path.abspath('.'), 'main.py')
],
    binaries=binaries,
    datas=[
        ('doc/VERSION', RESOURCES_DIR),
        ('doc/ACKNOWLEDGEMENTS.html', RESOURCES_DIR),
        # ('doc/LICENSE.PyQt5', RESOURCES_DIR),
        ('doc/LICENSE.html',  RESOURCES_DIR),
        ('resources/Subtitles.png', RESOURCES_DIR), ],
    hiddenimports=[
        'pythonopensubtitles'
],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher)
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
