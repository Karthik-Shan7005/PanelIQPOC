"""
Panel-IQ Build Script
======================
Produces a standalone Windows exe that serves the React frontend
and FastAPI backend — no Electron, no Node.js runtime required.

Steps:
  1. Build React frontend  (npm run build → frontend/dist)
  2. Compile Python backend with bundled frontend  (PyInstaller)

Output:
  dist/Panel-IQ.exe   — double-click to run; opens browser automatically
"""

import json
import os
import shutil
import subprocess
import sys

ROOT     = os.path.dirname(os.path.abspath(__file__))
BACKEND  = os.path.join(ROOT, 'backend')
FRONTEND = os.path.join(ROOT, 'frontend')
DIST     = os.path.join(ROOT, 'dist')


def run(cmd, cwd=None, label=''):
    print(f'\n{"="*60}')
    print(f'  {label or cmd}')
    print(f'{"="*60}')
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f'\nERROR: Step failed (exit code {result.returncode}). Aborting.')
        sys.exit(result.returncode)


def resolve_paneliq_python():
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
run('npm run build', cwd=FRONTEND, label='Step 1/2 — Building React frontend (Vite)')

FRONTEND_DIST = os.path.join(FRONTEND, 'dist')
if not os.path.isdir(FRONTEND_DIST):
    sys.exit('ERROR: frontend/dist not found after npm build.')
print(f'[ok] Frontend built: {FRONTEND_DIST}')

# ── Step 2: Compile Python backend (with bundled frontend) ───────────────────
for folder in ['build', 'dist']:
    target = os.path.join(BACKEND, folder)
    if os.path.exists(target):
        shutil.rmtree(target)

ENV_ROOT  = os.path.dirname(PANELIQ_PYTHON)
LIBSSL    = os.path.join(ENV_ROOT, 'Library', 'bin', 'libssl-3-x64.dll')
LIBCRYPTO = os.path.join(ENV_ROOT, 'Library', 'bin', 'libcrypto-3-x64.dll')

for dll in [LIBSSL, LIBCRYPTO]:
    if not os.path.isfile(dll):
        sys.exit(f'ERROR: Required OpenSSL DLL not found: {dll}')
print('[ok] OpenSSL DLLs found: libssl-3-x64.dll, libcrypto-3-x64.dll')

run(
    f'"{PANELIQ_PYTHON}" -m PyInstaller main.py '
    '--name "Panel-IQ" '
    '--onefile '
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
    '--exclude-module=tkinter '
    f'--add-binary "{LIBSSL};." '
    f'--add-binary "{LIBCRYPTO};." '
    f'--add-data "{FRONTEND_DIST};frontend" ',
    cwd=BACKEND,
    label='Step 2/2 — Compiling backend + bundling frontend (PyInstaller)'
)

# ── Copy output to dist/ ──────────────────────────────────────────────────────
os.makedirs(DIST, exist_ok=True)
src_exe = os.path.join(BACKEND, 'dist', 'Panel-IQ.exe')
dst_exe = os.path.join(DIST, 'Panel-IQ.exe')
shutil.copy2(src_exe, dst_exe)
size_mb = os.path.getsize(dst_exe) / 1_048_576

print('\n' + '='*60)
print('  BUILD COMPLETE')
print(f'  App:       dist/Panel-IQ.exe  ({size_mb:.0f} MB)')
print(f'  Prereqs:   dist/Panel-IQ Prerequisites.exe  (run once per machine)')
print('='*60)
