"""
PanelIQ Setup Assistant
One-time prerequisites wizard for demo machines.
Handles: ODBC Driver 17 check/install + paneliq.env creation.
"""

import os
import sys
import subprocess
import winreg
from pathlib import Path

import customtkinter as ctk
from tkinter import messagebox

ctk.set_appearance_mode("dark")

# ── Palette (matches PanelIQ dark theme) ─────────────────────────────────────
ACCENT  = "#00d4ff"
ACCENT2 = "#7c6af7"
BG      = "#0a0d14"
BG2     = "#111520"
BORDER  = "#1e2a40"
TEXT    = "#e8edf5"
MUTED   = "#6b7a99"
GREEN   = "#00e5a0"
RED     = "#ff6b6b"

APPDATA_DIR = Path(os.environ.get("APPDATA", "")) / "PanelIQ"

# ── Pre-fill defaults (overridden by wizard_config.env if bundled) ────────────
DEFAULTS = {
    "ANTHROPIC_API_KEY": "",
    "DB_SERVER":   "10.20.30.12",
    "DB_NAME":     "KpiReports",
    "DB_USER":     "",
    "DB_PASSWORD": "",
    "DB_DRIVER":   "ODBC Driver 17 for SQL Server",
}


def _load_defaults():
    if getattr(sys, "frozen", False):
        cfg = Path(sys._MEIPASS) / "wizard_config.env"
    else:
        cfg = Path(__file__).parent / "wizard_config.env"
    if cfg.exists():
        for line in cfg.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                DEFAULTS[k.strip()] = v.strip()


_load_defaults()

_ALL_PREFILLED = all(
    DEFAULTS.get(k)
    for k in ("ANTHROPIC_API_KEY", "DB_SERVER", "DB_NAME", "DB_USER", "DB_PASSWORD")
)


# ── ODBC helpers ──────────────────────────────────────────────────────────────

def check_odbc_installed() -> bool:
    try:
        winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 17 for SQL Server",
        )
        return True
    except FileNotFoundError:
        return False


def bundled_odbc_msi() -> Path | None:
    if getattr(sys, "frozen", False):
        p = Path(sys._MEIPASS) / "msodbcsql.msi"
    else:
        p = Path(__file__).parent / "setup_wizard" / "assets" / "msodbcsql.msi"
    return p if p.exists() else None


def install_odbc_silently(msi_path: Path) -> bool:
    r = subprocess.run(
        ["msiexec", "/i", str(msi_path), "/quiet", "/norestart",
         "IACCEPTMSODBCSQLLICENSETERMS=YES"],
        capture_output=True,
    )
    return r.returncode == 0


def write_env_file() -> Path:
    APPDATA_DIR.mkdir(parents=True, exist_ok=True)
    env_path = APPDATA_DIR / "paneliq.env"
    env_path.write_text(
        f"ANTHROPIC_API_KEY={DEFAULTS['ANTHROPIC_API_KEY']}\n"
        f"DB_SERVER={DEFAULTS['DB_SERVER']}\n"
        f"DB_NAME={DEFAULTS['DB_NAME']}\n"
        f"DB_USER={DEFAULTS['DB_USER']}\n"
        f"DB_PASSWORD={DEFAULTS['DB_PASSWORD']}\n"
        f"DB_DRIVER={DEFAULTS['DB_DRIVER']}\n",
        encoding="utf-8",
    )
    return env_path


def find_main_installer() -> Path | None:
    base = (Path(sys.executable).parent
            if getattr(sys, "frozen", False)
            else Path(__file__).parent / "desktop" / "dist-electron")
    for p in sorted(base.glob("PanelIQ Setup*.exe")):
        return p
    return None


# ── Wizard ────────────────────────────────────────────────────────────────────

class SetupWizard(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("PanelIQ — Setup Assistant")
        self.geometry("560x500")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        self._page       = 0
        self._odbc_ok    = check_odbc_installed()
        self._env_saved  = False

        # If all credentials pre-filled, skip configure page (pages: 0, 1, 3)
        self._pages = (
            [self._pg_welcome, self._pg_prereqs, self._pg_done]
            if _ALL_PREFILLED
            else [self._pg_welcome, self._pg_prereqs, self._pg_configure, self._pg_done]
        )

        self._build_header()
        self._content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self._content.pack(fill="both", expand=True, padx=28)
        self._build_footer()
        self._render()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=BG2, corner_radius=0, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="Panel", font=ctk.CTkFont(size=19, weight="bold"),
                     text_color=TEXT).pack(side="left", padx=(20, 0))
        ctk.CTkLabel(hdr, text="IQ", font=ctk.CTkFont(size=19, weight="bold"),
                     text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(hdr, text="  Setup Assistant",
                     font=ctk.CTkFont(size=12), text_color=MUTED).pack(side="left")

        step_names = (["Welcome", "Prerequisites", "Done"]
                      if _ALL_PREFILLED
                      else ["Welcome", "Prerequisites", "Configure", "Done"])
        self._step_row = ctk.CTkFrame(hdr, fg_color=BG2)
        self._step_row.pack(side="right", padx=20)
        for i, name in enumerate(step_names):
            ctk.CTkLabel(self._step_row,
                         text=f" {i+1}. {name} ",
                         font=ctk.CTkFont(size=10),
                         text_color=MUTED).pack(side="left")

    def _build_footer(self):
        ftr = ctk.CTkFrame(self, fg_color=BG2, corner_radius=0, height=56)
        ftr.pack(fill="x", side="bottom")
        ftr.pack_propagate(False)

        self._btn_back = ctk.CTkButton(
            ftr, text="← Back", width=100, height=34,
            fg_color=BORDER, hover_color="#2a3a50", text_color=TEXT,
            command=self._go_back)
        self._btn_back.pack(side="left", padx=20, pady=11)

        self._btn_next = ctk.CTkButton(
            ftr, text="Next →", width=120, height=34,
            fg_color=ACCENT, hover_color=ACCENT2,
            text_color=BG, font=ctk.CTkFont(weight="bold"),
            command=self._go_next)
        self._btn_next.pack(side="right", padx=20, pady=11)

    def _update_step_indicators(self):
        for i, lbl in enumerate(self._step_row.winfo_children()):
            lbl.configure(text_color=ACCENT if i == self._page else MUTED)

    def _render(self):
        for w in self._content.winfo_children():
            w.destroy()
        self._pages[self._page]()
        self._btn_back.configure(state="normal" if self._page > 0 else "disabled")
        is_last = self._page == len(self._pages) - 1
        self._btn_next.configure(
            text="Finish" if is_last else "Next →",
            fg_color=GREEN if is_last else ACCENT,
            text_color=BG,
        )
        self._update_step_indicators()

    def _go_next(self):
        is_last = self._page == len(self._pages) - 1
        if is_last:
            self.quit()
            return

        # Validate prerequisites page
        if self._pages[self._page] == self._pg_prereqs and not self._odbc_ok:
            messagebox.showwarning(
                "Driver Required",
                "Please install ODBC Driver 17 for SQL Server before continuing.")
            return

        # Auto-save config if all pre-filled and we're about to leave prereqs
        if self._pages[self._page] == self._pg_prereqs and _ALL_PREFILLED:
            self._do_save_env()

        # Validate configure page
        if self._pages[self._page] == self._pg_configure:
            if not self._validate_and_save():
                return

        self._page += 1
        self._render()

    def _go_back(self):
        if self._page > 0:
            self._page -= 1
            self._render()

    # ── Pages ─────────────────────────────────────────────────────────────────

    def _pg_welcome(self):
        f = self._content
        ctk.CTkLabel(f, text="Welcome to PanelIQ",
                     font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT).pack(pady=(32, 6))
        ctk.CTkLabel(f, text="AI-Powered Panel Intelligence",
                     font=ctk.CTkFont(size=13), text_color=MUTED).pack()
        ctk.CTkFrame(f, fg_color=BORDER, height=1).pack(fill="x", pady=22)

        steps = ("1.  Check & install the required database driver\n"
                 "2.  Save your connection settings automatically\n"
                 "3.  Launch the PanelIQ installer")
        if _ALL_PREFILLED:
            steps = ("1.  Check & install the required database driver\n"
                     "2.  Save connection settings (pre-configured)\n"
                     "3.  Launch the PanelIQ installer")

        ctk.CTkLabel(
            f, text="This wizard sets up your machine in 2 quick steps:\n\n" + steps,
            font=ctk.CTkFont(size=13), text_color=TEXT, justify="left",
        ).pack(anchor="w", padx=4)

        ctk.CTkFrame(f, fg_color=BORDER, height=1).pack(fill="x", pady=22)
        ctk.CTkLabel(
            f,
            text="Note: BA network or VPN is required when using the app\n"
                 "(not needed for this setup).",
            font=ctk.CTkFont(size=11), text_color=MUTED, justify="left",
        ).pack(anchor="w", padx=4)

    def _pg_prereqs(self):
        f = self._content
        ctk.CTkLabel(f, text="Step 1 — Prerequisites",
                     font=ctk.CTkFont(size=17, weight="bold"), text_color=TEXT).pack(pady=(22, 4), anchor="w")
        ctk.CTkLabel(
            f,
            text="PanelIQ needs Microsoft ODBC Driver 17 to connect to the panel database.",
            font=ctk.CTkFont(size=12), text_color=MUTED, wraplength=500, justify="left",
        ).pack(anchor="w")

        ctk.CTkFrame(f, fg_color=BORDER, height=1).pack(fill="x", pady=16)

        card = ctk.CTkFrame(f, fg_color=BG2, corner_radius=10)
        card.pack(fill="x", pady=4)

        status_text = ("✓  ODBC Driver 17 for SQL Server — Installed"
                       if self._odbc_ok
                       else "✗  ODBC Driver 17 for SQL Server — Not Found")
        ctk.CTkLabel(card, text=status_text,
                     font=ctk.CTkFont(size=13),
                     text_color=GREEN if self._odbc_ok else RED).pack(
            side="left", padx=16, pady=14)

        if not self._odbc_ok:
            ctk.CTkButton(
                card, text="Install Now", width=110, height=30,
                fg_color=ACCENT, hover_color=ACCENT2,
                text_color=BG, font=ctk.CTkFont(weight="bold"),
                command=self._install_odbc,
            ).pack(side="right", padx=12, pady=10)

        ctk.CTkLabel(
            f,
            text="All other dependencies are bundled inside the PanelIQ installer.",
            font=ctk.CTkFont(size=11), text_color=MUTED,
        ).pack(pady=(16, 0), anchor="w")

    def _install_odbc(self):
        msi = bundled_odbc_msi()
        if msi:
            messagebox.showinfo("Installing", "Installing ODBC Driver 17 silently…\nThis may take a moment.")
            ok = install_odbc_silently(msi)
            if not ok:
                messagebox.showerror("Install Failed",
                                     "Silent install failed.\n"
                                     "Please run msodbcsql.msi manually and click Refresh.")
        else:
            import webbrowser
            webbrowser.open("https://go.microsoft.com/fwlink/?linkid=2249006")
            messagebox.showinfo(
                "Download ODBC Driver",
                "The Microsoft download page has opened in your browser.\n\n"
                "1. Download  msodbcsql.msi\n"
                "2. Run it and accept the licence\n"
                "3. Click OK here — the wizard will re-check automatically.",
            )
        self._odbc_ok = check_odbc_installed()
        self._render()

    def _pg_configure(self):
        f = self._content
        ctk.CTkLabel(f, text="Step 2 — Configuration",
                     font=ctk.CTkFont(size=17, weight="bold"), text_color=TEXT).pack(pady=(22, 4), anchor="w")
        ctk.CTkLabel(
            f, text="Enter your Anthropic API key. Database settings are pre-configured.",
            font=ctk.CTkFont(size=12), text_color=MUTED,
        ).pack(anchor="w")
        ctk.CTkFrame(f, fg_color=BORDER, height=1).pack(fill="x", pady=14)

        def row(label, default="", masked=False, locked=False):
            r = ctk.CTkFrame(f, fg_color=BG)
            r.pack(fill="x", pady=3)
            ctk.CTkLabel(r, text=label, font=ctk.CTkFont(size=11),
                         text_color=MUTED, width=130, anchor="w").pack(side="left")
            e = ctk.CTkEntry(r, width=310, height=30,
                             fg_color=BORDER if locked else BG2,
                             border_color=BORDER,
                             text_color=MUTED if locked else TEXT,
                             show="•" if masked else "")
            e.insert(0, default)
            if locked:
                e.configure(state="disabled")
            e.pack(side="left", padx=(8, 0))
            return e

        self._e_api  = row("Anthropic API Key", DEFAULTS["ANTHROPIC_API_KEY"], masked=True)
        row("DB Server",    DEFAULTS["DB_SERVER"],   locked=True)
        row("Database",     DEFAULTS["DB_NAME"],     locked=True)
        row("DB Username",  DEFAULTS["DB_USER"],     locked=True)
        row("DB Password",  DEFAULTS["DB_PASSWORD"], masked=True, locked=True)

        if self._env_saved:
            ctk.CTkLabel(f, text="✓  Configuration saved",
                         font=ctk.CTkFont(size=11), text_color=GREEN).pack(pady=(10, 0), anchor="w")

    def _validate_and_save(self) -> bool:
        api_key = self._e_api.get().strip()
        if not api_key:
            messagebox.showwarning("API Key Required",
                                   "Please enter your Anthropic API Key to continue.")
            return False
        DEFAULTS["ANTHROPIC_API_KEY"] = api_key
        return self._do_save_env()

    def _do_save_env(self) -> bool:
        try:
            write_env_file()
            self._env_saved = True
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not save configuration:\n{e}")
            return False

    def _pg_done(self):
        f = self._content
        ctk.CTkLabel(f, text="You're all set!", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=GREEN).pack(pady=(32, 6))
        ctk.CTkLabel(f, text="PanelIQ is ready to install on this machine.",
                     font=ctk.CTkFont(size=13), text_color=MUTED).pack()
        ctk.CTkFrame(f, fg_color=BORDER, height=1).pack(fill="x", pady=22)

        checks = ["✓  ODBC Driver 17 for SQL Server — installed",
                  "✓  Connection settings saved to AppData"]
        for line in checks:
            ctk.CTkLabel(f, text=line, font=ctk.CTkFont(size=12),
                         text_color=GREEN, justify="left").pack(anchor="w", padx=4, pady=2)

        ctk.CTkFrame(f, fg_color=BORDER, height=1).pack(fill="x", pady=20)

        installer = find_main_installer()
        if installer:
            ctk.CTkButton(
                f,
                text=f"Launch  {installer.name}",
                width=280, height=42,
                fg_color=ACCENT, hover_color=ACCENT2,
                text_color=BG, font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda: (subprocess.Popen([str(installer)]), self.quit()),
            ).pack(pady=4)
        else:
            ctk.CTkLabel(
                f,
                text="Now run  PanelIQ Setup 1.0.0.exe  from the same folder.",
                font=ctk.CTkFont(size=13), text_color=ACCENT,
            ).pack(anchor="w", padx=4)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = SetupWizard()
    app.mainloop()
