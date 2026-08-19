import subprocess
import shutil
import os
import platform
import sys
import argparse
import configparser
from pathlib import Path


def load_config():
    config = configparser.ConfigParser()
    config_path = Path(__file__).resolve().parent / "packaging.ini"
    config.read(config_path, encoding="utf-8")
    return config


def setup_target_vendor(target_name: str, python_interpreter: str, target_dir: str, packages: list, platform_tag: str = 'win_amd64'):
    """Vendors packages for a specific Python target environment."""
    os.makedirs(target_dir, exist_ok=True)
    print(f"📦 Vendoring for target '{target_name}' into {target_dir} using {python_interpreter}...")

    pip_args = [
        python_interpreter, '-m', 'pip', 'install',
        '--no-user',
        '--target', target_dir,
    ]
    if platform_tag:
        pip_args.extend(['--platform', platform_tag, '--only-binary=:all:'])
    pip_args.extend(packages)

    try:
        subprocess.check_call(pip_args)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Warning: Direct binary pip install failed ({e}). Falling back without --platform/--only-binary...")
        fallback_args = [
            python_interpreter, '-m', 'pip', 'install',
            '--no-user',
            '--target', target_dir,
        ] + packages
        subprocess.check_call(fallback_args)


def setup_vendor(dual_target: bool = True, python_version: str = None):
    config = load_config()
    
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    vendor_dir = os.path.join(project_root, 'IntelliFiller', 'vendor')
    
    if os.path.exists(vendor_dir):
        shutil.rmtree(vendor_dir)
    os.makedirs(vendor_dir, exist_ok=True)

    packages_str = config.get("vendor", "packages", fallback="")
    packages = [p.strip() for p in packages_str.split("\n") if p.strip()]

    py39_exe = config.get("release", "python39_interpreter", fallback=r"C:\Python\Python39\python.exe").strip()
    py313_exe = config.get("release", "python313_interpreter", fallback=r"C:\Python\Python313\python.exe").strip()
    default_exe = config.get("release", "python_interpreter", fallback=sys.executable).strip()

    if not os.path.exists(py39_exe):
        py39_exe = default_exe
    if not os.path.exists(py313_exe):
        py313_exe = default_exe

    if dual_target:
        # Target A: Python 3.9 for Anki 24.x
        py39_dir = os.path.join(vendor_dir, "py39")
        setup_target_vendor("py39", py39_exe, py39_dir, packages, platform_tag='win_amd64')

        # Target B: Python 3.13 for Anki 25/26.x
        py313_dir = os.path.join(vendor_dir, "py313")
        setup_target_vendor("py313", py313_exe, py313_dir, packages, platform_tag='win_amd64')

        # Legacy / fallback win32 directory pointing to py313
        win32_dir = os.path.join(vendor_dir, "win32")
        setup_target_vendor("win32", py313_exe, win32_dir, packages, platform_tag='win_amd64')
    else:
        target_dir = os.path.join(vendor_dir, "win32")
        setup_target_vendor("default", default_exe, target_dir, packages, platform_tag='win_amd64')

    # Remove unnecessary files to keep vendor directory slim
    for root, dirs, files in os.walk(vendor_dir, topdown=False):
        for dir_name in list(dirs):
            if dir_name in {'tests', 'test', '__pycache__'} or dir_name.endswith('.dist-info'):
                try:
                    shutil.rmtree(os.path.join(root, dir_name))
                except Exception as e:
                    print(f"Warning cleaning {dir_name}: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Vendor third-party packages for IntelliFiller.")
    parser.add_argument(
        "--single-target",
        action="store_true",
        help="Vendor for single default target rather than dual py39/py313.",
    )
    parser.add_argument(
        "--python-version",
        default=None,
        help="Target Python version for Linux wheel selection.",
    )
    args = parser.parse_args()
    setup_vendor(dual_target=not args.single_target, python_version=args.python_version)
