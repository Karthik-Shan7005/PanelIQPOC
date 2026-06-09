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
    # FastAPI + Starlette (dynamic imports PyInstaller misses)
    '--hidden-import=fastapi '
    '--hidden-import=fastapi.responses '
    '--hidden-import=fastapi.middleware '
    '--hidden-import=fastapi.middleware.cors '
    '--hidden-import=starlette '
    '--hidden-import=starlette.routing '
    '--hidden-import=starlette.middleware '
    '--hidden-import=starlette.middleware.cors '
    '--hidden-import=starlette.responses '
    '--hidden-import=starlette.requests '
    '--hidden-import=starlette.datastructures '
    '--hidden-import=starlette.exceptions '
    '--hidden-import=starlette.background '
    # Pydantic
    '--hidden-import=pydantic '
    '--hidden-import=pydantic.deprecated.class_validators '
    '--hidden-import=pydantic.v1 '
    # Anthropic SDK
    '--hidden-import=anthropic '
    '--hidden-import=anthropic._models '
    '--hidden-import=httpx '
    # Database + env
    '--hidden-import=pyodbc '
    '--hidden-import=dotenv '
    '--hidden-import=python_dotenv '
    # Uvicorn
    '--hidden-import=uvicorn.logging '
    '--hidden-import=uvicorn.loops '
    '--hidden-import=uvicorn.loops.auto '
    '--hidden-import=uvicorn.protocols '
    '--hidden-import=uvicorn.protocols.http '
    '--hidden-import=uvicorn.protocols.http.auto '
    '--hidden-import=uvicorn.lifespan '
    '--hidden-import=uvicorn.lifespan.on '
    '--hidden-import=anyio '
    '--hidden-import=anyio._backends._asyncio '
    # Exclude heavy Anaconda packages genuinely not needed by this backend
    '--exclude-module=scipy '
    '--exclude-module=sklearn '
    '--exclude-module=matplotlib '
    '--exclude-module=PyQt5 '
    '--exclude-module=PyQt6 '
    '--exclude-module=tkinter '
    '--exclude-module=cv2 '
    '--exclude-module=torch '
    '--exclude-module=tensorflow '
    '--exclude-module=statsmodels '
    '--exclude-module=numba '
    '--exclude-module=llvmlite '
    '--exclude-module=plotly '
    '--exclude-module=bokeh '
    '--exclude-module=skimage '
    '--exclude-module=sympy '
    '--exclude-module=notebook '
    '--exclude-module=IPython '
    '--exclude-module=ipykernel '
    '--exclude-module=jupyter '
    '--exclude-module=altair '
    '--exclude-module=xarray '
    '--exclude-module=astropy '
    '--exclude-module=botocore '
    '--exclude-module=boto3 ',
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
