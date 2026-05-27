import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Anthropic API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# SQL Server Database config
DB_CONFIG = {
    "server":   os.getenv("DB_SERVER"),
    "database": os.getenv("DB_NAME"),
    "username": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "driver":   os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
}