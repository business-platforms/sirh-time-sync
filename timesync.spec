# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules

datas = [('assets', 'assets'), ('src', 'src'), ('version.txt', '.')]
hiddenimports = ['sqlite3', 'requests', 'zk', 'schedule', 'uuid', 'tkinter.simpledialog', 'pystray', 'PIL', 'psutil', 'pandas', 'pandas._libs.tslibs.timedeltas', 'pandas._libs.tslibs.np_datetime', 'pandas._libs.tslibs.nattype', 'pandas._libs.skiplist', 'pandas.io.formats.style', 'numpy', 'numpy.random.common', 'numpy.random.bounded_integers', 'numpy.random.entropy', 'openpyxl', 'openpyxl.workbook', 'openpyxl.worksheet.worksheet']
datas += collect_data_files('pandas')
hiddenimports += collect_submodules('pandas')
hiddenimports += collect_submodules('numpy')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'IPython', 'jupyter', 'notebook', 'tkinter.test'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='timesync',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
