import os
import subprocess
import sys
from pathlib import Path


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