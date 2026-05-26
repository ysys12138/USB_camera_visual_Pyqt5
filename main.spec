# main.spec - 修复版：防止 self-collecting

block_cipher = None

# === 关键：排除 build 和 dist 目录 ===
excluded_paths = [
    'build',
    'dist',
    '__pycache__',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('data', 'data'),       # 显式包含 data/
        ('.', '.'),             # 但注意：不会包含 build/ 和 dist/
    ],
    hiddenimports=[
        'app_config',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],  # 可加可不加
)

# 过滤掉 build 和 dist 下的文件
for d in a.datas:
    if any(part in ['build', 'dist'] for part in d[0].split(os.sep)):
        a.datas.remove(d)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='医学影像工作站.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False
)