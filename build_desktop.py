"""
PanelIQ Desktop Build Script
=============================
Produces a standalone Windows .exe installer for the COO demo.

Steps:
  1. Build React frontend  (npm run build)
  2. Compile Python backend  (PyInstaller)
  3. Install Electron deps  (npm install in desktop/)
  4. Package with electron-builder

Usage:
  python build_desktop.py

Output:
  desktop/dist-electron/PanelIQ Setup 1.0.0.exe
"""

import subprocess
import sys
import shutil
import os

ROOT    = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, 'backend')
FRONTEND = os.path.join(ROOT, 'frontend')
DESKTOP = os.path.join(ROOT, 'desktop')
BACKEND_DIST = os.path.join(DESKTOP, 'backend-dist')

def run(cmd, cwd=None, label=''):
    print(f'\n{"="*60}')
    print(f'  {label or cmd}')
    print(f'{"="*60}')
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f'\nERROR: Step failed (exit code {result.returncode}). Aborting.')
        sys.exit(result.returncode)

# ── Step 1: Build React frontend ─────────────────────────────────────────────
run('npm run build', cwd=FRONTEND, label='Step 1/4 — Building React frontend (Vite)')

# ── Step 2: Compile Python backend with PyInstaller ──────────────────────────
# Clear previous PyInstaller output
for folder in ['build', 'dist']:
    target = os.path.join(BACKEND, folder)
    if os.path.exists(target):
        shutil.rmtree(target)

run(
    'pyinstaller main.py '
    '--name paneliq_backend '
    '--onefile '
    '--noconsole '
    '--add-data ".env;." '
    '--hidden-import=uvicorn.logging '
    '--hidden-import=uvicorn.loops '
    '--hidden-import=uvicorn.loops.auto '
    '--hidden-import=uvicorn.protocols '
    '--hidden-import=uvicorn.protocols.http '
    '--hidden-import=uvicorn.protocols.http.auto '
    '--hidden-import=uvicorn.lifespan '
    '--hidden-import=uvicorn.lifespan.on '
    '--hidden-import=anyio '
    '--hidden-import=anyio._backends._asyncio',
    cwd=BACKEND,
    label='Step 2/4 — Compiling Python backend (PyInstaller)'
)

# Copy compiled backend exe to desktop/backend-dist/
if os.path.exists(BACKEND_DIST):
    shutil.rmtree(BACKEND_DIST)
os.makedirs(BACKEND_DIST)
src_exe = os.path.join(BACKEND, 'dist', 'paneliq_backend.exe')
shutil.copy2(src_exe, os.path.join(BACKEND_DIST, 'paneliq_backend.exe'))
print(f'Backend exe copied to desktop/backend-dist/')

# ── Step 3: Install Electron dependencies ────────────────────────────────────
run('npm install', cwd=DESKTOP, label='Step 3/4 — Installing Electron dependencies')

# ── Step 4: Package with electron-builder ────────────────────────────────────
run('npm run build:win', cwd=DESKTOP, label='Step 4/4 — Packaging with electron-builder')

print('\n' + '='*60)
print('  BUILD COMPLETE')
print(f'  Installer: desktop/dist-electron/PanelIQ Setup 1.0.0.exe')
print('='*60)
