"""
PanelIQ Setup Assistant
Uses Windows native TaskDialog (comctl32) — no Tcl/Tk, no third-party GUI.
Works on any Windows 10/11 machine regardless of other software installed.
"""

import ctypes
import ctypes.wintypes as wt
import json
import os
import subprocess
import sys
import winreg
from pathlib import Path

# ── Windows API constants ────────────────────────────────────────────────────
IDOK     = 1
IDCANCEL = 2
IDYES    = 6
IDNO     = 7
IDCLOSE  = 8

MB_OK              = 0x00000000
MB_OKCANCEL        = 0x00000001
MB_YESNO           = 0x00000004
MB_ICONINFORMATION = 0x00000040
MB_ICONWARNING     = 0x00000030
MB_ICONERROR       = 0x00000010
MB_TOPMOST         = 0x00040000

# TaskDialog common button flags
TDCBF_OK_BUTTON     = 0x0001
TDCBF_YES_BUTTON    = 0x0002
TDCBF_NO_BUTTON     = 0x0004
TDCBF_CANCEL_BUTTON = 0x0008
TDCBF_CLOSE_BUTTON  = 0x0020

# TaskDialog icons (passed as resource IDs cast to PCWSTR)
TD_WARNING_ICON     = ctypes.cast(65535, ctypes.c_wchar_p)
TD_ERROR_ICON       = ctypes.cast(65534, ctypes.c_wchar_p)
TD_INFORMATION_ICON = ctypes.cast(65533, ctypes.c_wchar_p)
TD_SHIELD_ICON      = ctypes.cast(65532, ctypes.c_wchar_p)

APP_TITLE = "PanelIQ Setup Assistant"

APPDATA_DIR = Path(os.environ.get("APPDATA", "")) / "PanelIQ"

# ── Credentials (loaded from bundled wizard_config.env) ───────────────────────
DEFAULTS = {
    "ANTHROPIC_API_KEY": "",
    "DB_SERVER":   "10.20.30.12",
    "DB_NAME":     "KpiReports",
    "DB_USER":     "",
    "DB_PASSWORD": "",
    "DB_DRIVER":   "ODBC Driver 17 for SQL Server",
}


def _load_defaults():
    cfg = (Path(sys._MEIPASS) / "wizard_config.env"
           if getattr(sys, "frozen", False)
           else Path(__file__).parent / "wizard_config.env")
    if cfg.exists():
        for line in cfg.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                DEFAULTS[k.strip()] = v.strip()


_load_defaults()


# ── Dialog helpers ────────────────────────────────────────────────────────────

def _msgbox(text: str, title: str = APP_TITLE, flags: int = MB_OK | MB_ICONINFORMATION) -> int:
    return ctypes.windll.user32.MessageBoxW(0, text, title, flags | MB_TOPMOST)


def _task_dialog(main: str, content: str = "", buttons: int = TDCBF_OK_BUTTON,
                 icon=None) -> int:
    """Thin wrapper around TaskDialog (comctl32 v6). Falls back to MessageBox."""
    if icon is None:
        icon = TD_INFORMATION_ICON
    result = ctypes.c_int(0)
    hr = ctypes.windll.comctl32.TaskDialog(
        None, None,
        APP_TITLE, main, content or None,
        buttons, icon,
        ctypes.byref(result),
    )
    if hr != 0:                                    # fallback if TaskDialog unavailable
        flags = MB_OK | MB_ICONINFORMATION
        if buttons & TDCBF_CANCEL_BUTTON:
            flags = MB_OKCANCEL | MB_ICONINFORMATION
        return _msgbox(f"{main}\n\n{content}", flags=flags)
    return result.value


# ── ODBC helpers ──────────────────────────────────────────────────────────────

def check_odbc() -> bool:
    try:
        winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 17 for SQL Server",
        )
        return True
    except FileNotFoundError:
        return False


def bundled_msi() -> Path | None:
    base = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).parent / "setup_wizard" / "assets"
    p = (Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).parent / "setup_wizard" / "assets") / "msodbcsql.msi"
    return p if p.exists() else None


def install_odbc(msi: Path) -> bool:
    r = subprocess.run(
        ["msiexec", "/i", str(msi), "/quiet", "/norestart",
         "IACCEPTMSODBCSQLLICENSETERMS=YES"],
        capture_output=True,
    )
    return r.returncode == 0


# ── Env file writer ───────────────────────────────────────────────────────────

def write_env() -> Path:
    APPDATA_DIR.mkdir(parents=True, exist_ok=True)
    p = APPDATA_DIR / "paneliq.env"
    p.write_text(
        "\n".join([
            f"ANTHROPIC_API_KEY={DEFAULTS['ANTHROPIC_API_KEY']}",
            f"DB_SERVER={DEFAULTS['DB_SERVER']}",
            f"DB_NAME={DEFAULTS['DB_NAME']}",
            f"DB_USER={DEFAULTS['DB_USER']}",
            f"DB_PASSWORD={DEFAULTS['DB_PASSWORD']}",
            f"DB_DRIVER={DEFAULTS['DB_DRIVER']}",
        ]) + "\n",
        encoding="utf-8",
    )
    return p


def find_main_installer() -> Path | None:
    base = (Path(sys.executable).parent
            if getattr(sys, "frozen", False)
            else Path(__file__).parent / "desktop" / "dist-electron")
    for p in sorted(base.glob("PanelIQ Setup*.exe")):
        return p
    return None


# ── Wizard flow ───────────────────────────────────────────────────────────────

def run():
    # ── Page 1: Welcome ───────────────────────────────────────────────────────
    btn = _task_dialog(
        "Welcome to PanelIQ",
        "This assistant will prepare your machine to run PanelIQ in two quick steps:\n\n"
        "  1.  Install Microsoft ODBC Driver 17 for SQL Server (if needed)\n"
        "  2.  Save your connection settings automatically\n\n"
        "Click OK to begin. The whole process takes under 2 minutes.",
        buttons=TDCBF_OK_BUTTON | TDCBF_CANCEL_BUTTON,
        icon=TD_INFORMATION_ICON,
    )
    if btn == IDCANCEL:
        return

    # ── Page 2: ODBC Driver ───────────────────────────────────────────────────
    odbc_installed = check_odbc()

    if odbc_installed:
        _task_dialog(
            "ODBC Driver 17 — Already Installed",
            "Microsoft ODBC Driver 17 for SQL Server is already installed on this machine.\n\n"
            "No action needed. Click OK to continue.",
            icon=TD_INFORMATION_ICON,
        )
    else:
        msi = bundled_msi()
        if msi:
            _task_dialog(
                "Installing ODBC Driver 17...",
                "Microsoft ODBC Driver 17 for SQL Server was not found.\n\n"
                "Click OK to install it silently. This may take up to a minute.\n"
                "You may see a UAC (User Account Control) prompt — please click Yes.",
                icon=TD_INFORMATION_ICON,
            )
            ok = install_odbc(msi)
            if not ok or not check_odbc():
                _task_dialog(
                    "Installation Failed",
                    "The ODBC Driver 17 installation did not complete successfully.\n\n"
                    "Please ask your IT team to install:\n"
                    "  Microsoft ODBC Driver 17 for SQL Server (x64)\n\n"
                    "Then run this setup again.",
                    icon=TD_ERROR_ICON,
                )
                return
            _task_dialog(
                "ODBC Driver 17 Installed",
                "Microsoft ODBC Driver 17 for SQL Server was installed successfully.",
                icon=TD_INFORMATION_ICON,
            )
        else:
            _task_dialog(
                "ODBC Driver 17 Not Found",
                "Microsoft ODBC Driver 17 for SQL Server is required but was not found.\n\n"
                "Please download and install it:\n"
                "  Search: 'Download ODBC Driver 17 for SQL Server' on Microsoft's website\n\n"
                "After installing, run this setup again.",
                icon=TD_WARNING_ICON,
            )
            return

    # ── Page 3: Write config ──────────────────────────────────────────────────
    if not DEFAULTS.get("ANTHROPIC_API_KEY"):
        _task_dialog(
            "Configuration Error",
            "The Anthropic API key is missing from this setup package.\n\n"
            "Please contact the person who provided this installer.",
            icon=TD_ERROR_ICON,
        )
        return

    try:
        env_path = write_env()
    except Exception as e:
        _task_dialog(
            "Could Not Save Configuration",
            f"An error occurred while saving the connection settings:\n\n{e}",
            icon=TD_ERROR_ICON,
        )
        return

    # ── Page 4: Done ──────────────────────────────────────────────────────────
    installer = find_main_installer()
    launch_prompt = (
        "\n\nClick Yes to launch the PanelIQ installer now, or No to close."
        if installer else
        "\n\nYou can now run  PanelIQ Setup 1.0.0.exe  from the same folder."
    )

    btn = _task_dialog(
        "Setup Complete!",
        "Your machine is ready to run PanelIQ.\n\n"
        "  ✓   ODBC Driver 17 for SQL Server\n"
        "  ✓   Connection settings saved\n"
        + launch_prompt,
        buttons=(TDCBF_YES_BUTTON | TDCBF_NO_BUTTON) if installer else TDCBF_OK_BUTTON,
        icon=TD_INFORMATION_ICON,
    )

    if installer and btn == IDYES:
        subprocess.Popen([str(installer)])


if __name__ == "__main__":
    run()
