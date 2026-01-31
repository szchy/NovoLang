# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['editor.py'],
    pathex=['C:\\Users\\test\\trae file（Pro）\\NovoLang\\local_packages'],
    binaries=[],
    datas=[('python', 'python')],
    hiddenimports=['pyautogui', 'pygetwindow'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='NovoLangEditor',
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
