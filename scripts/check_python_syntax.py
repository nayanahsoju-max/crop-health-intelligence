"""Compile project Python sources in memory without writing bytecode files."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = ("alembic", "backend", "scripts", "src", "tests")


def main() -> int:
    checked = 0
    for directory in SOURCE_DIRS:
        for path in sorted((ROOT / directory).rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
            checked += 1
    print(f"Python syntax check passed for {checked} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
