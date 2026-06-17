"""
Build script for PanelIQ Setup Assistant wizard.

Usage:
  1. Fill in wizard_config.env with credentials (copy wizard_config.env.template)
  2. Optionally place msodbcsql.msi in setup_wizard/assets/
  3. Run:  python build_setup_wizard.py

Output:
  dist/PanelIQ Prerequisites.exe   (single-file, ~30 MB)
"""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def resolve_python():
    override = os.environ.get("PANELIQ_PYTHON")
    if override and os.path.isfile(override):
        return override
    try:
        out = subprocess.check_output(
            "conda env list --json", shell=True, text=True, stderr=subprocess.DEVNULL
        )
        for envdir in json.loads(out).get("envs", []):
            if os.path.basename(envdir).lower() == "paneliq":
                py = os.path.join(envdir, "python.exe")
                if os.path.isfile(py):
                    return py
    except Exception:
        pass
    fallback = r"C:\Users\KarthikShanmugam\.anaconda\envs\paneliq\python.exe"
    if os.path.isfile(fallback):
        return fallback
    sys.exit(
        "ERROR: Could not find the paneliq conda env.\n"
        "  Set PANELIQ_PYTHON to the python.exe path and retry."
    )


PYTHON = resolve_python()
print(f"[ok] Using Python: {PYTHON}")

# ── Ensure customtkinter is available ────────────────────────────────────────
print("[..] Checking customtkinter...")
r = subprocess.run(
    [PYTHON, "-c", "import customtkinter"],
    capture_output=True,
)
if r.returncode != 0:
    print("[..] Installing customtkinter...")
    subprocess.run([PYTHON, "-m", "pip", "install", "customtkinter", "--quiet"], check=True)
print("[ok] customtkinter ready")

# ── Extra data files ──────────────────────────────────────────────────────────
add_data_args = []

wizard_config = os.path.join(ROOT, "wizard_config.env")
if os.path.isfile(wizard_config):
    add_data_args += ["--add-data", f"{wizard_config};."]
    print("[ok] Bundling wizard_config.env (pre-filled credentials)")
else:
    print(
        "[warn] wizard_config.env not found — credentials will not be pre-filled.\n"
        "       Copy wizard_config.env.template → wizard_config.env and fill in values."
    )

odbc_msi = os.path.join(ROOT, "setup_wizard", "assets", "msodbcsql.msi")
if os.path.isfile(odbc_msi):
    add_data_args += ["--add-data", f"{odbc_msi};."]
    print("[ok] Bundling msodbcsql.msi (silent ODBC install)")
else:
    print("[info] msodbcsql.msi not found — wizard will open download page if driver missing")

# ── Icon ──────────────────────────────────────────────────────────────────────
icon = os.path.join(ROOT, "desktop", "assets", "icon.ico")
icon_args = ["--icon", icon] if os.path.isfile(icon) else []

# ── PyInstaller command ───────────────────────────────────────────────────────
cmd = [
    PYTHON, "-m", "PyInstaller",
    os.path.join(ROOT, "setup_wizard.py"),
    "--name", "PanelIQ Prerequisites",
    "--onefile",
    "--noconsole",
    "--collect-all=customtkinter",
    "--distpath", os.path.join(ROOT, "dist"),
    "--workpath", os.path.join(ROOT, "build_wizard"),
    "--specpath", os.path.join(ROOT, "build_wizard"),
] + icon_args + add_data_args

print(f'\n{"="*60}')
print("  Building PanelIQ Setup Assistant...")
print(f'{"="*60}\n')

result = subprocess.run(cmd, cwd=ROOT)
if result.returncode != 0:
    sys.exit(f"ERROR: Wizard build failed (exit {result.returncode})")

out_exe = os.path.join(ROOT, "dist", "PanelIQ Prerequisites.exe")
size_mb = round(os.path.getsize(out_exe) / 1_048_576, 1) if os.path.isfile(out_exe) else "?"

print(f'\n{"="*60}')
print("  WIZARD BUILD COMPLETE")
print(f"  Output : dist/PanelIQ Prerequisites.exe  ({size_mb} MB)")
print()
print("  Demo package:")
print("    dist/PanelIQ Prerequisites.exe")
print("    desktop/dist-electron/PanelIQ Setup 1.0.0.exe")
print(f'{"="*60}')
