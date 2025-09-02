from rich.console import Console
from pathlib import Path
from dotenv import load_dotenv
import os

HOME = str(Path.home())

# loading variables from .env file
load_dotenv(Path.home().joinpath(".env.cibutler"))

LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
if LOGLEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    LOGLEVEL = "INFO"

DEBUG = False
if "DEBUG" in LOGLEVEL:
    # Log level set to DEBUG, this will produce a lot of output, use with caution
    DEBUG = True
    console = Console(log_path=False, record=True)
    error_console = Console(stderr=True, style="bold red", record=True)
else:
    console = Console(log_path=False)
    error_console = Console(stderr=True, style="bold red")


def save_console_text():
    if DEBUG:
        console.print("Saving console output to files...")
        console.save_text(f"{HOME}/cibutler.console.txt")
        error_console.save_text(f"{HOME}/cibutler.error_console.txt")
