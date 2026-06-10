import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def _load_env():
    if getattr(sys, 'frozen', False):
        # Packaged exe: look for paneliq.env next to the exe, then in %APPDATA%\PanelIQ\
        candidates = [
            Path(sys.executable).parent / 'paneliq.env',
            Path(os.environ.get('APPDATA', '')) / 'PanelIQ' / 'paneliq.env',
        ]
        for path in candidates:
            if path.exists():
                load_dotenv(path)
                return
        # Nothing found — env vars may still be set by the OS; proceed and let
        # missing-key errors surface at the point of use.
    else:
        load_dotenv()  # dev: reads backend/.env


_load_env()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

DB_CONFIG = {
    "server":   os.getenv("DB_SERVER"),
    "database": os.getenv("DB_NAME"),
    "username": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "driver":   os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
}
