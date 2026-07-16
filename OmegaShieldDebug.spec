# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['backend\\run.py'],
    pathex=['backend'],
    binaries=[],
    datas=[('backend/app/models/threat_model.pkl', 'app/models'), ('frontend/dist', 'frontend/dist')],
    hiddenimports=['uvicorn.protocols.http.httptools_impl', 'uvicorn.protocols.http.h11_impl', 'uvicorn.protocols.websockets.websockets_impl', 'uvicorn.protocols.websockets.wsproto_impl', 'uvicorn.lifespan.on', 'aiosqlite', 'sqlalchemy.dialects.sqlite.aiosqlite', 'passlib.handlers.bcrypt'],
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
    [],
    exclude_binaries=True,
    name='OmegaShieldDebug',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OmegaShieldDebug',
)
