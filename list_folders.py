#!/usr/bin/env python3
# list_folders.py - Viser innholdet på reMarkable Cloud via rmapi
#
# Bruk:
#   python list_folders.py           # vis rotmappe
#   python list_folders.py /Nyheter  # vis spesifikk mappe

import subprocess
import sys
from pathlib import Path

RMAPI = str(Path(__file__).parent / "rmapi")


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "/"
    result = subprocess.run(
        [RMAPI, "-ni", "ls", folder],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        print(f"FEIL: {result.stderr or result.stdout}")
        sys.exit(1)
    print(result.stdout)


if __name__ == "__main__":
    main()
