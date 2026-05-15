#!/usr/bin/env python3
"""
validate_dot_d2.py

Offline syntax validator for Graphviz DOT and D2 diagrams.

Usage:
    python validate_dot_d2.py demo.dot
    python validate_dot_d2.py arch.d2

Behavior:
- DOT: uses `dot -Tsvg` dry-run parsing
- D2 : uses `d2 --check`
"""

import subprocess
import sys
import tempfile
from pathlib import Path

SUPPORTED = {".dot", ".gv", ".d2"}


def run_command(cmd):
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"


def validate_dot(path: Path):
    # Use a temporary output file to avoid collisions in concurrent runs.
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        code, _, err = run_command(["dot", "-Tsvg", str(path), "-o", tmp_path])
        if code == 0:
            print(f"[OK] Graphviz DOT syntax valid: {path.name}")
            return 0

        print(f"[ERROR] DOT syntax invalid: {path.name}")
        print(err.strip())
        return 1
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass


def validate_d2(path: Path):
    code, out, err = run_command(["d2", "--check", str(path)])
    if code == 0:
        print(f"[OK] D2 syntax valid: {path.name}")
        return 0

    print(f"[ERROR] D2 syntax invalid: {path.name}")
    print((err or out).strip())
    return 1


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_dot_d2.py <diagram.dot|diagram.d2>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        sys.exit(1)

    suffix = path.suffix.lower()

    if suffix not in SUPPORTED:
        print(f"[ERROR] Unsupported file type: {suffix}")
        sys.exit(1)

    if suffix in {".dot", ".gv"}:
        sys.exit(validate_dot(path))

    if suffix == ".d2":
        sys.exit(validate_d2(path))


if __name__ == "__main__":
    main()
