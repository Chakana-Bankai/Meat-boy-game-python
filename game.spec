# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['game/main.py'], pathex=[], binaries=[], datas=[('game/levels', 'game/levels')], hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='meatboy_py', debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=True)
