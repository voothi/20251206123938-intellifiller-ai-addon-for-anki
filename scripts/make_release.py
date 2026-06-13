#!/usr/bin/env python3
"""Main developer entry point to compile/package the Anki addon.

Delegates execution to scripts/packaging/release_pipeline.py.
"""

import sys
import subprocess
from pathlib import Path


def main():
    script_dir = Path(__file__).resolve().parent
    pipeline_script = script_dir / "packaging" / "release_pipeline.py"
    
    if not pipeline_script.exists():
        print(f"Error: Release pipeline script not found at {pipeline_script}")
        sys.exit(1)

    cmd = [sys.executable, str(pipeline_script)] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
