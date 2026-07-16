# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['backend\\run.py'],
    pathex=['backend'],
    binaries=[],
    datas=[('D:\\Omega\\backend\\app\\models\\threat_model.pkl', 'app/models'), ('D:\\Omega\\frontend\\dist', 'frontend/dist')],
    hiddenimports=['uvicorn.protocols.http.httptools_impl', 'uvicorn.protocols.http.h11_impl', 'uvicorn.protocols.websockets.websockets_impl', 'uvicorn.protocols.websockets.wsproto_impl', 'uvicorn.lifespan.on', 'aiosqlite', 'sqlalchemy.dialects.sqlite.aiosqlite', 'passlib.handlers.bcrypt', 'scipy', 'scipy.special', 'scipy.linalg', 'sklearn', 'sklearn.ensemble', 'sklearn.model_selection', 'sklearn.tree', 'sklearn.utils', 'pandas', 'numpy', 'networkx', 'matplotlib', 'matplotlib.pyplot', 'plotly', 'plotly.graph_objects', 'PIL', 'app.main', 'app.routers.plant', 'app.routers.plc', 'app.routers.communication', 'app.routers.security', 'app.routers.risk', 'app.routers.recovery', 'app.routers.audit', 'app.routers.health', 'app.routers.attack', 'app.routers.ai', 'app.routers.trust', 'app.services.cloud_agent_bridge'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'sphinx', 'bokeh', 'h5py', 'lz4', 'distributed', 'panel', 'skimage', 'docutils', 'jedi', 'IPython', 'ipykernel', 'notebook', 'nbconvert', 'tornado', 'astropy', 'astropy_iers_data', 'zope', 'pyarrow'],
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
    name='OmegaAI',
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
    icon=['omega_logo.ico'],
)
