"""Platform-independent release pipeline orchestrator for IntelliFiller.

Cleans and sets up vendor dependencies, executes the full test suite, and
packages the Anki addon into a timestamped ``.ankiaddon`` file.
"""

import argparse
import os
import subprocess
import sys
import configparser
from pathlib import Path


def load_config():
    config = configparser.ConfigParser()
    config_path = Path(__file__).resolve().parent / "packaging.ini"
    config.read(config_path, encoding="utf-8")
    return config


def run_pipeline(output_dir: str) -> int:
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
            fallback_dir = Path(__file__).resolve().parent.parent.parent / "dist"
            print(f"[INFO] Falling back to local directory: {fallback_dir}")
            try:
                fallback_dir.mkdir(parents=True, exist_ok=True)
                out_path = fallback_dir
            except OSError as ex:
                print(f"[ERROR] Could not create fallback directory: {ex}")
                return 1

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    config = load_config()
    python_interpreter = config.get("release", "python_interpreter", fallback="").strip()
    if not python_interpreter:
        python_interpreter = sys.executable

    steps_str = config.get("pipeline", "steps", fallback="setup_local_vendor.py\npytest\ncreate_addon_zip.py")
    steps = [s.strip() for s in steps_str.split("\n") if s.strip()]

    for step in steps:
        if step == "pytest":
            print("[INFO] Running test suite...")
            rc = subprocess.call([python_interpreter, "-m", "pytest"], cwd=str(project_root))
            if rc != 0:
                print(f"[ERROR] Tests failed with error code {rc}. Aborting release creation.")
                return rc
        else:
            script_path = script_dir / step
            if not script_path.exists():
                print(f"[ERROR] Step script not found at {script_path}")
                return 1

            if step == "create_addon_zip.py":
                cmd = [python_interpreter, str(script_path), "--out", str(out_path)]
            else:
                cmd = [python_interpreter, str(script_path)]

            print(f"[INFO] Executing step: {step}...")
            rc = subprocess.call(cmd)
            if rc != 0:
                print(f"[ERROR] Step '{step}' failed with error code {rc}. Aborting release creation.")
                return rc

    print()
    print("[SUCCESS] Release pipeline complete.")
    return 0


def main() -> int:
    config = load_config()
    default_output_dir = config.get("release", "default_output_dir", fallback="")

    parser = argparse.ArgumentParser(
        description="Platform-independent IntelliFiller release pipeline."
    )
    parser.add_argument(
        "--out",
        dest="output_dir",
        default=os.environ.get("INTELLIFILLER_RELEASE_DIR", default_output_dir),
        help="Output directory for the .ankiaddon file (default: %(default)s).",
    )
    args = parser.parse_args()
    return run_pipeline(args.output_dir)


if __name__ == "__main__":
    sys.exit(main())
