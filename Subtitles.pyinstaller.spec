# -*- mode: python -*-

from PyInstaller.utils.hooks import collect_dynamic_libs

import os
import sys
import re
from os import path

block_cipher = None

# Defaults to .app/Contents/Resources on macOS
RESOURCES_DIR = '.'


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
        ('doc/VERSION', RESOURCES_DIR),
        ('doc/LICENSE.PyQt5', RESOURCES_DIR),
        ('LICENSE',  RESOURCES_DIR),
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
          strip=False,
          upx=True,
          console=False)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Subtitles')
app = BUNDLE(coll,
             name='Subtitles.app',
             icon='resources/Subtitles.icns',
             bundle_identifier='io.github.philipbel.subtitles',
             info_plist={
                 'NSHighResolutionCapable': 'True'
             })
