#!/usr/bin/env bash

set +e

echo "=================================================="
echo " Telegram Ad Userbot - Project Check"
echo "=================================================="
echo

echo "[1] System"
echo "OS:     $(uname -s)"
echo "Kernel: $(uname -r)"
echo "Arch:   $(uname -m)"
echo

echo "[2] Python"
python3 --version
echo "Python path: $(command -v python3)"
echo

echo "[3] Project"
pwd
echo

echo "[4] Project tree"
if command -v tree >/dev/null 2>&1; then
    tree -a -I '.git|.venv|__pycache__|*.pyc|data'
else
    find . \
        -not -path './.git/*' \
        -not -path './.venv/*' \
        -not -path './__pycache__/*' \
        -not -path './data/*' \
        -type f | sort
fi
echo

echo "[5] Required files"
for file in \
    ".env.example" \
    ".gitignore" \
    "README.md" \
    "README.fa.md" \
    "requirements.txt" \
    "setup.py" \
    "run.py" \
    "src/__init__.py" \
    "src/main.py" \
    "src/config.py" \
    "src/telegram/__init__.py" \
    "src/telegram/client.py" \
    "src/telegram/dialogs.py" \
    "src/telegram/handlers.py" \
    "src/database/__init__.py" \
    "src/database/db.py" \
    "src/campaign/__init__.py" \
    "src/campaign/manager.py"
do
    if [ -f "$file" ]; then
        echo "PASS  $file"
    else
        echo "FAIL  $file"
    fi
done
echo

echo "[6] Forbidden tracked/runtime files"
for path in ".env" "data" ".venv"; do
    if [ -e "$path" ]; then
        echo "INFO  $path exists locally (this can be normal)"
    else
        echo "OK    $path not present"
    fi
done
echo

echo "[7] Environment file safety"
if [ -f ".env" ]; then
    echo "WARNING: .env exists locally."
    echo "Checking whether .env contains the expected keys:"
    grep -E '^(TELEGRAM_API_ID|TELEGRAM_API_HASH|TELEGRAM_SESSION_NAME)=' .env \
        | sed 's/=.*$/=<hidden>/'
else
    echo "OK: .env does not exist."
fi
echo

echo "[8] Gitignore"
if [ -f ".gitignore" ]; then
    cat .gitignore
else
    echo "FAIL: .gitignore missing"
fi
echo

echo "[9] Requirements"
cat requirements.txt 2>/dev/null || echo "FAIL: requirements.txt missing"
echo

echo "[10] Syntax check"
python3 -m compileall -q src run.py setup.py
if [ $? -eq 0 ]; then
    echo "PASS: Python syntax"
else
    echo "FAIL: Python syntax"
fi
echo

echo "[11] Import check"
PYTHONPATH="$PWD" python3 - <<'PY'
import sys

modules = [
    "src.config",
    "src.database.db",
    "src.telegram.client",
    "src.telegram.dialogs",
    "src.telegram.handlers",
    "src.campaign.manager",
]

failed = False

for module in modules:
    try:
        __import__(module)
        print(f"PASS  {module}")
    except Exception as exc:
        failed = True
        print(f"FAIL  {module}: {type(exc).__name__}: {exc}")

sys.exit(1 if failed else 0)
PY
echo

echo "[12] Dependency check"
PYTHONPATH="$PWD" python3 - <<'PY'
packages = [
    ("pyrogram", "pyrogram"),
    ("tgcrypto", "tgcrypto"),
    ("python-dotenv", "dotenv"),
]

failed = False

for label, module in packages:
    try:
        imported = __import__(module)
        version = getattr(imported, "__version__", "unknown")
        print(f"PASS  {label}: {version}")
    except Exception as exc:
        failed = True
        print(f"FAIL  {label}: {exc}")

raise SystemExit(1 if failed else 0)
PY
echo

echo "[13] Database initialization check"
python3 - <<'PY'
import tempfile
from pathlib import Path

from src.database.db import Database

with tempfile.TemporaryDirectory() as tmp:
    db_path = Path(tmp) / "test.db"
    db = Database(db_path)

    required_tables = {
        "settings",
        "targets",
        "campaigns",
        "campaign_targets",
        "events",
    }

    rows = db.conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table'"
    ).fetchall()

    actual_tables = {row["name"] for row in rows}

    missing = required_tables - actual_tables

    if missing:
        print("FAIL: missing tables:", ", ".join(sorted(missing)))
        raise SystemExit(1)

    print("PASS: database schema")
PY
echo

echo "[14] Config validation"
if [ -f ".env" ]; then
    PYTHONPATH="$PWD" python3 - <<'PY'
from src.config import validate_config

try:
    validate_config()
    print("PASS: configuration")
except Exception as exc:
    print(f"FAIL: configuration: {type(exc).__name__}: {exc}")
    raise SystemExit(1)
PY
else
    echo "SKIP: .env not present"
fi
echo

echo "[15] Git status"
if [ -d ".git" ]; then
    git status --short
    echo
    echo "Tracked sensitive/runtime files:"
    git ls-files | grep -E '(^\.env$|^data/|\.session$|\.session-journal$|^\.venv/)' \
        || echo "NONE"
else
    echo "Git repository not initialized yet."
fi
echo

echo "=================================================="
echo " CHECK COMPLETE"
echo "=================================================="
