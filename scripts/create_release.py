"""Platform-independent release packager for IntelliFiller.

Replaces the legacy Windows-only ``scripts/create_release.cmd``. Running this
script on Windows, macOS or Linux will ensure the output directory exists,
invoke ``scripts/package_addon.py`` and produce a timestamped ``.ankiaddon``
file.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_OUTPUT_DIR = r"C:\Users\voothi\Documents\20251206191819-intellifilter-publication"


def run_release(output_dir: str) -> int:
    # Strip trailing path separators for cross-platform cleanliness.
    output_dir = output_dir.rstrip(r"\/").strip()
    if not output_dir:
        print("[ERROR] Output directory is required.")
        return 1

    print()
    print(f"[INFO] Saving release to: \"{output_dir}\"")
    print()

    out_path = Path(output_dir)
    if not out_path.exists():
        print("[INFO] Directory not found. Creating...")
        try:
            out_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"[WARNING] Could not create output directory '{output_dir}': {e}")
            fallback_dir = Path(__file__).resolve().parent.parent / "dist"
            print(f"[INFO] Falling back to local directory: {fallback_dir}")
            try:
                fallback_dir.mkdir(parents=True, exist_ok=True)
                out_path = fallback_dir
            except OSError as ex:
                print(f"[ERROR] Could not create fallback directory: {ex}")
                return 1

    script_dir = Path(__file__).resolve().parent
    package_script = script_dir / "package_addon.py"
    if not package_script.exists():
        print(f"[ERROR] package_addon.py not found at {package_script}")
        return 1

    cmd = [sys.executable, str(package_script), "--out", str(out_path)]
    print(f"[INFO] Running: {' '.join(cmd)}")
    rc = subprocess.call(cmd)
    if rc != 0:
        print()
        print(f"[ERROR] Packaging failed with error code {rc}")
        return rc

    print()
    print("[SUCCESS] Done.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Platform-independent IntelliFiller release packager."
    )
    parser.add_argument(
        "--out",
        dest="output_dir",
        default=os.environ.get("INTELLIFILLER_RELEASE_DIR", DEFAULT_OUTPUT_DIR),
        help="Output directory for the .ankiaddon file (default: %(default)s).",
    )
    args = parser.parse_args()
    return run_release(args.output_dir)


if __name__ == "__main__":
    sys.exit(main())
