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

  Optional env vars:
    PANELIQ_PYTHON   — path to python.exe in the paneliq conda env
                       (auto-detected via `conda env list` if not set)

Output:
  desktop/dist-electron/PanelIQ Setup 1.0.0.exe
"""

import json
import os
import shutil
import subprocess
import sys

ROOT         = os.path.dirname(os.path.abspath(__file__))
BACKEND      = os.path.join(ROOT, 'backend')
FRONTEND     = os.path.join(ROOT, 'frontend')
DESKTOP      = os.path.join(ROOT, 'desktop')
BACKEND_DIST = os.path.join(DESKTOP, 'backend-dist')


def run(cmd, cwd=None, label=''):
    print(f'\n{"="*60}')
    print(f'  {label or cmd}')
    print(f'{"="*60}')
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f'\nERROR: Step failed (exit code {result.returncode}). Aborting.')
        sys.exit(result.returncode)


def resolve_paneliq_python():
    """Return path to the paneliq conda env's python.exe.
    Priority: PANELIQ_PYTHON env var → conda env list → fail with instructions."""
    override = os.environ.get('PANELIQ_PYTHON')
    if override:
        if os.path.isfile(override):
            return override
        sys.exit(f'ERROR: PANELIQ_PYTHON is set to "{override}" but that file does not exist.')

    try:
        out = subprocess.check_output(
            'conda env list --json', shell=True, text=True, stderr=subprocess.DEVNULL
        )
        for envdir in json.loads(out).get('envs', []):
            if os.path.basename(envdir).lower() == 'paneliq':
                py = os.path.join(envdir, 'python.exe')
                if os.path.isfile(py):
                    return py
    except Exception as e:
        print(f'WARN: conda lookup failed ({e}) — falling back to known path')

    # Last resort: known path on this machine
    fallback = r'C:\Users\KarthikShanmugam\.anaconda\envs\paneliq\python.exe'
    if os.path.isfile(fallback):
        return fallback

    sys.exit(
        "ERROR: Could not locate the 'paneliq' conda env.\n"
        "  Create it:  conda create -n paneliq python=3.11\n"
        "              conda activate paneliq\n"
        "              pip install -r backend/requirements.txt\n"
        "  Or set:     $env:PANELIQ_PYTHON = 'C:\\path\\to\\python.exe'"
    )


# ── Resolve + validate Python env ────────────────────────────────────────────
PANELIQ_PYTHON = resolve_paneliq_python()
print(f'\n[ok] Using Python: {PANELIQ_PYTHON}')

check = subprocess.run(
    [PANELIQ_PYTHON, '-c', 'import fastapi, uvicorn, anthropic, pyodbc, pandas'],
    capture_output=True, text=True
)
if check.returncode != 0:
    sys.exit(
        f'ERROR: paneliq env is missing required packages:\n{check.stderr}\n'
        f'Run:  "{PANELIQ_PYTHON}" -m pip install -r backend/requirements.txt'
    )
print('[ok] All backend dependencies found in paneliq env')

# ── Step 1: Build React frontend ─────────────────────────────────────────────
run('npm run build', cwd=FRONTEND, label='Step 1/4 — Building React frontend (Vite)')

# ── Step 2: Compile Python backend with PyInstaller ──────────────────────────
for folder in ['build', 'dist']:
    target = os.path.join(BACKEND, folder)
    if os.path.exists(target):
        shutil.rmtree(target)

run(
    f'"{PANELIQ_PYTHON}" -m PyInstaller main.py '
    '--name paneliq_backend '
    '--onefile '
    '--noconsole '
    # NOTE: .env is NOT bundled — secrets are read from %APPDATA%\PanelIQ\paneliq.env
    # collect-all bundles entire packages including submodules + data files
    '--collect-all=fastapi '
    '--collect-all=starlette '
    '--collect-all=pydantic '
    '--collect-all=pydantic_core '
    '--collect-all=anthropic '
    '--collect-all=httpx '
    '--collect-all=httpcore '
    '--collect-all=uvicorn '
    '--collect-all=anyio '
    '--collect-all=dotenv '
    '--collect-all=pandas '
    '--collect-all=numpy '
    '--hidden-import=pyodbc '
    '--hidden-import=anyio._backends._asyncio '
    '--exclude-module=tkinter ',
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
