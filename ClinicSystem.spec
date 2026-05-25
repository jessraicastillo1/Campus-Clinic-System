# ClinicSystem.spec
# PyInstaller spec file — bundles pgpc_logo.jpg and pgpc_bg.jpg inside the exe.
# Usage: pyinstaller ClinicSystem.spec

from PyInstaller.utils.hooks import collect_all
import os

block_cipher = None

# Collect everything PyQt6 needs
datas_qt, binaries_qt, hiddenimports_qt = collect_all('PyQt6')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries_qt,
    datas=[
        # Bundle the images inside the exe
        ('pgpc_logo.jpg', '.'),
        ('pgpc_bg.jpg',   '.'),
    ] + datas_qt,
    hiddenimports=hiddenimports_qt + [
        'backend',
        'backend.auth',
        'backend.config',
        'backend.database',
        'backend.dashboard_stats',
        'backend.inventory',
        'backend.models',
        'backend.queue_logic',
        'backend.utils',
        'ui',
        'ui.login_window',
        'ui.dashboard_window',
        'ui.pages',
        'ui.pages.home_page',
        'ui.pages.queue_page',
        'ui.pages.vitals_page',
        'ui.pages.appointments_page',
        'ui.pages.absences_page',
        'ui.pages.audit_page',
        'ui.pages.vaccines_page',
        'ui.pages.table_page',
        'ui.pages.base_page',
        'ui.pages.history_page',
        'ui.pages.inventory_page',
        'ui.pages.emergency_page',
        'ui.pages.incidents_page',
        'ui.pages.clearances_page',
        'ui.pages.referrals_page',
        'ui.pages.dispense_page',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ClinicSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # No black console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='pgpc_logo.ico',  # Uncomment and convert logo to .ico if you want a taskbar icon
)
