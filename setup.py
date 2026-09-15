import getpass
import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
VENV_DIR = ROOT_DIR / ".venv"
ENV_FILE = ROOT_DIR / ".env"
REQUIREMENTS_FILE = ROOT_DIR / "requirements.txt"


def get_venv_python() -> Path:

    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"

    return VENV_DIR / "bin" / "python"


def run_command(
    command: list[str],
) -> None:

    subprocess.run(
        command,
        cwd=ROOT_DIR,
        check=True,
    )


def create_virtual_environment() -> Path:

    python_path = get_venv_python()

    if python_path.exists():

        print(
            "✓ Virtual environment already exists."
        )

        return python_path

    print(
        "Creating virtual environment..."
    )

    run_command(
        [
            sys.executable,
            "-m",
            "venv",
            str(VENV_DIR),
        ]
    )

    print(
        "✓ Virtual environment created."
    )

    return python_path


def install_dependencies(
    python_path: Path,
) -> None:

    print(
        "Installing dependencies..."
    )

    run_command(
        [
            str(python_path),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
        ]
    )

    run_command(
        [
            str(python_path),
            "-m",
            "pip",
            "install",
            "-r",
            str(REQUIREMENTS_FILE),
        ]
    )

    print(
        "✓ Dependencies installed."
    )


def create_env_file() -> None:

    if ENV_FILE.exists():

        print(
            "✓ .env already exists."
        )

        return

    print()
    print(
        "Telegram API configuration"
    )
    print("-" * 30)

    api_id = input(
        "Telegram API ID: "
    ).strip()

    api_hash = getpass.getpass(
        "Telegram API Hash: "
    ).strip()

    if not api_id:
        raise ValueError(
            "API ID cannot be empty."
        )

    if not api_hash:
        raise ValueError(
            "API Hash cannot be empty."
        )

    ENV_FILE.write_text(
        (
            f"TELEGRAM_API_ID={api_id}\n"
            f"TELEGRAM_API_HASH={api_hash}\n"
            "TELEGRAM_SESSION_NAME="
            "telegram_ad_userbot\n"
        ),
        encoding="utf-8",
    )

    print(
        "✓ .env created."
    )


def create_data_directory() -> None:

    data_dir = ROOT_DIR / "data"

    data_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "✓ Data directory ready."
    )


def main() -> None:

    print()
    print("=" * 50)
    print("Telegram Ad Userbot Setup")
    print("=" * 50)
    print()

    if sys.version_info < (3, 11):

        raise RuntimeError(
            "Python 3.11 or newer is required."
        )

    print(
        f"Python "
        f"{sys.version_info.major}."
        f"{sys.version_info.minor}."
        f"{sys.version_info.micro} detected."
    )

    python_path = (
        create_virtual_environment()
    )

    install_dependencies(
        python_path
    )

    create_data_directory()
    create_env_file()

    print()
    print("=" * 50)
    print("Setup complete.")
    print("=" * 50)
    print()
    print(
        "Run the application with:"
    )
    print()
    print(
        "    python run.py"
    )
    print()


if __name__ == "__main__":
    main()