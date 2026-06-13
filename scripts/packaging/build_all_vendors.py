import subprocess
import shutil
import os
import sys
import configparser
from pathlib import Path


def load_config():
    config = configparser.ConfigParser()
    config_path = Path(__file__).resolve().parent / "packaging.ini"
    config.read(config_path, encoding="utf-8")
    return config


def build_all_platforms():
    config = load_config()
    
    # Get path to vendor directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    vendor_dir = os.path.join(project_root, 'IntelliFiller', 'vendor')
    
    # Clean/create vendor directory
    if os.path.exists(vendor_dir):
        shutil.rmtree(vendor_dir)
    os.makedirs(vendor_dir)

    python_interpreter = config.get("release", "python_interpreter", fallback="").strip()
    if not python_interpreter:
        python_interpreter = sys.executable

    platforms = config.items("platforms")
    
    packages_str = config.get("vendor", "packages", fallback="")
    packages = [p.strip() for p in packages_str.split("\n") if p.strip()]
    
    for platform_tag, dir_name in platforms:
        platform_dir = os.path.join(vendor_dir, dir_name)
        os.makedirs(platform_dir, exist_ok=True)
        
        print(f"Building for {platform_tag}...")
        subprocess.check_call([
            python_interpreter, '-m', 'pip', 'install',
            '--no-user',
            '--platform', platform_tag,
            '--target', platform_dir,
            '--only-binary=:all:',
        ] + packages)


if __name__ == '__main__':
    build_all_platforms()
