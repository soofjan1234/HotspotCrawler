# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 项目根目录
project_root = os.path.abspath('.')

# 收集数据文件
datas = []
datas += collect_data_files('src', excludes=['__pycache__', 'old'])

# 添加配置文件和HTML文件
config_files = [
    ('src/config/config.yml', 'src/config'),
    ('src/web/index.html', 'src/web'),
]

for src, dst in config_files:
    if os.path.exists(src):
        datas.append((src, dst))

# 收集隐藏导入
hiddenimports = [
    'src.config.config_manager',
    'src.crawlers.toutiao_crawler',
    'src.crawlers.article_extractor',
    'src.crawlers.media_downloader',
    'src.crawlers.article_manager',
    'src.utils.log_utils',
    'src.utils.scheduler_manager',
    'src.utils.ai_generator',
    'src.utils.pyinstaller_utils',
    'selenium',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.chrome.options',
    'selenium.webdriver.common.by',
    'webdriver_manager',
    'webdriver_manager.chrome',
    'bs4',
    'yaml',
    'apscheduler',
    'flask',
    'flask.templating',
    'flask.stream_with_context',
    'requests',
    'queue',
    'threading',
    'datetime',
    'json',
    'platform',
    'tempfile',
    'subprocess',
]

# 分析主脚本
a = Analysis(
    ['src/web/app.py'],
    pathex=[project_root, os.path.join(project_root, 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'test', 'tests', 'PIL', 'matplotlib', 'numpy', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 确保包含所有必要的模块
for mod in a.pure:
    if 'src' in str(mod):
        print(f"Including module: {mod}")

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HotspotCrawler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)