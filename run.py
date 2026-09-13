import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
VENV_DIR = ROOT_DIR / ".venv"


def get_venv_python() -> Path:
    """Return the Python executable inside the local virtual environment."""

    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"

    return VENV_DIR / "bin" / "python"


def main() -> None:

    venv_python = get_venv_python()

    # اگر برنامه هنوز داخل virtual environment اجرا نشده،
    # آن را با Python محیط پروژه دوباره اجرا می‌کنیم.
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

    # اجرای مستقیم از داخل venv
    from src.main import main as application_main

    application_main()


if __name__ == "__main__":
    main()