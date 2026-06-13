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


def setup_vendor(python_version=None):
    config = load_config()
    if python_version is None:
        python_version = config.get("release", "python_version", fallback="3.13")

    # Create/clean vendor directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    vendor_dir = os.path.join(project_root, 'IntelliFiller', 'vendor')
    if os.path.exists(vendor_dir):
        shutil.rmtree(vendor_dir)
    os.makedirs(vendor_dir)

    # Determine python interpreter
    python_interpreter = config.get("release", "python_interpreter", fallback="").strip()
    if not python_interpreter:
        python_interpreter = sys.executable

    # Determine platform-specific pip arguments
    pip_args = [python_interpreter, '-m', 'pip', 'install', '--no-user', '--target', vendor_dir]

    system = platform.system().lower()
    machine = platform.machine().lower()

    # Platform-specific handling
    if system == 'darwin':  # macOS
        if machine == 'arm64':
            pip_args.extend(['--platform', 'macosx_11_0_arm64'])
            pip_args.append('--only-binary=:all:')
        else:  # Intel Mac
            pip_args.extend(['--platform', 'macosx_10_15_x86_64'])
            pip_args.append('--only-binary=:all:')
    elif system == 'windows':
        pip_args.extend(['--platform', 'win_amd64'])
        pip_args.append('--only-binary=:all:')
    elif system == 'linux':
        # Linux wheel targeting uses the requested python version
        pip_args.extend([
            '--platform', 'manylinux2014_x86_64',
            '--python-version', python_version,
            '--only-binary=:all:',
        ])

    # Add the packages from config
    packages_str = config.get("vendor", "packages", fallback="")
    packages = [p.strip() for p in packages_str.split("\n") if p.strip()]
    pip_args.extend(packages)

    try:
        subprocess.check_call(pip_args)
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        print("Attempting fallback installation without platform specification...")
        fallback_args = [
            python_interpreter, '-m', 'pip', 'install', '--no-user', '--target', vendor_dir,
        ] + packages
        subprocess.check_call(fallback_args)

    # Remove unnecessary files to keep vendor directory slim
    for root, dirs, files in os.walk(vendor_dir):
        for dir_name in dirs:
            if dir_name in {'tests', 'test', '__pycache__', '*.dist-info'}:
                shutil.rmtree(os.path.join(root, dir_name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Vendor third-party packages for IntelliFiller.")
    parser.add_argument(
        "--python-version",
        default=None,
        help="Target Python version for Linux wheel selection.",
    )
    args = parser.parse_args()
    setup_vendor(python_version=args.python_version)
