import asyncio
import os
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------
# Python 3.14 compatibility bootstrap.
#
# Python 3.14 removed implicit event-loop creation from
# asyncio.get_event_loop(). Hydrogram 0.2.0 still calls it
# during Client.__init__, so we must ensure a loop exists
# BEFORE Hydrogram is imported.
# ---------------------------------------------------------

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


ROOT_DIR = Path(__file__).resolve().parent
VENV_DIR = ROOT_DIR / ".venv"


def get_venv_python() -> Path:

    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"

    return VENV_DIR / "bin" / "python"


def main() -> None:

    venv_python = get_venv_python()

    if sys.prefix == sys.base_prefix:

        if not venv_python.exists():

            print(
                "Virtual environment not found.\n"
                "Please run setup.py first."
            )

            raise SystemExit(1)

        subprocess.run(
            [
                str(venv_python),
                "-m",
                "src.main",
            ],
            cwd=ROOT_DIR,
            check=True,
        )

        return

    from src.main import main as application_main

    application_main()


if __name__ == "__main__":
    main()
