import subprocess
import shutil
import os
import platform
import sys
import argparse


def setup_vendor(python_version="3.13"):
    # Create/clean vendor directory
    vendor_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'IntelliFiller', 'vendor')
    if os.path.exists(vendor_dir):
        shutil.rmtree(vendor_dir)
    os.makedirs(vendor_dir)

    # Determine platform-specific pip arguments
    pip_args = [sys.executable, '-m', 'pip', 'install', '--no-user', '--target', vendor_dir]

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

    # Add the packages.
    # Note: openai and httpx are intentionally removed; the addon uses urllib.request now.
    pip_args.extend([
        'typing_extensions>=4.7.0',
        'pydantic',
        'pyzipper'
    ])

    try:
        subprocess.check_call(pip_args)
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        print("Attempting fallback installation without platform specification...")
        # Fallback to simple install without platform specification
        fallback_args = [
            sys.executable, '-m', 'pip', 'install', '--no-user', '--target', vendor_dir,
            'pyzipper',
        ]
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
        default="3.13",
        help="Target Python version for Linux wheel selection (default: 3.13).",
    )
    args = parser.parse_args()
    setup_vendor(python_version=args.python_version)
