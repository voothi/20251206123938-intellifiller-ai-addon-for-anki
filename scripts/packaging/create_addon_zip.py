import os
import sys
import zipfile
import argparse
import configparser
from datetime import datetime
from pathlib import Path


def load_config():
    config = configparser.ConfigParser()
    config_path = Path(__file__).resolve().parent / "packaging.ini"
    config.read(config_path, encoding="utf-8")
    return config


def create_addon_package(output_dir: str = None):
    config = load_config()
    
    excluded_root_files_str = config.get("exclusions", "root_files", fallback="meta.json")
    excluded_root_files = set(p.strip() for p in excluded_root_files_str.split("\n") if p.strip())
    
    excluded_dir_names_str = config.get("exclusions", "dir_names", fallback="user_files\n__pycache__\n.git")
    excluded_dir_names = set(p.strip() for p in excluded_dir_names_str.split("\n") if p.strip())

    # Determine paths
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    addon_source_dir = project_root / "IntelliFiller"
    
    if not addon_source_dir.exists():
        print(f"Error: Addon source directory not found at {addon_source_dir}")
        sys.exit(1)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}-intellifiller-ai-addon-for-anki.ankiaddon"
    
    if output_dir:
        output_path = Path(output_dir) / filename
    else:
        output_path = project_root / filename

    print(f"📦 Packaging addon...")
    print(f"   Source: {addon_source_dir}")
    print(f"   Dest:   {output_path}")

    # Create ZIP
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(addon_source_dir):
                # Warn if 'user_files' appears in subdirectories (e.g. vendor) before we exclude it
                if "user_files" in dirs and Path(root) != addon_source_dir:
                    rel_path = Path(root).relative_to(addon_source_dir) / "user_files"
                    print(f"⚠️  NOTICE: Found and SKIPPED 'user_files' directory in subfolder: {rel_path}")

                # 1. Directory Exclusion (In-place modification)
                # This prevents descending into user_files, __pycache__, etc.
                dirs[:] = [d for d in dirs if d not in excluded_dir_names]
                
                for file in files:
                    full_path = Path(root) / file
                    relative_path = full_path.relative_to(addon_source_dir)
                    
                    # 2. Specific Root File Exclusions
                    # e.g. meta.json is only excluded if it's in the root
                    if str(relative_path) in excluded_root_files:
                        print(f"   Skipping root file: {relative_path}")
                        continue
                    
                    # 3. Block sensitive files if they somehow appear in root (safety net)
                    # We rely on 'user_files' directory exclusion for the main config files.
                    # But if credentials.json is accidentally at root, exclude it.
                    if len(relative_path.parts) == 1 and file in {"credentials.json", "settings.json"}:
                         print(f"   Skipping sensitive file at root: {relative_path}")
                         continue

                    # 4. General Safety: Skip .pyc files everywhere
                    if file.endswith(".pyc") or file.endswith(".pyo"):
                        continue

                    # 5. WARN about sensitive-looking files that are being INCLUDED (e.g. inside vendor)
                    if file in {"credentials.json", "settings.json", "meta.json"}:
                        print(f"⚠️  NOTICE: Including potentially sensitive file (found in subfolder): {relative_path}")

                    zf.write(full_path, arcname=relative_path)
                    
        print(f"✅ Package created successfully!")
        
        # Verify exclusions
        print("🔍 Verifying package content...")
        with zipfile.ZipFile(output_path, 'r') as zf:
            file_list = zf.namelist()
            issues_found = False
            for f in file_list:
                # Check strict forbidden dirs
                for forbidden_dir in excluded_dir_names:
                    if f.startswith(f"{forbidden_dir}/") or f == forbidden_dir:
                        print(f"❌ WARNING: Forbidden directory found in zip: {f}")
                        issues_found = True
                
                # Check root files
                if f in excluded_root_files:
                     print(f"❌ WARNING: Excluded root file found: {f}")
                     issues_found = True

            if not issues_found:
                print("✅ Verification passed: Sensitive paths excluded.")
            else:
                print("⚠️  Verification failed! Check the output.")

    except Exception as e:
        print(f"❌ Error creating package: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Package IntelliFiller addon for Anki.")
    parser.add_argument("--out", type=str, help="Optional output directory for the .ankiaddon file")
    
    args = parser.parse_args()
    create_addon_package(args.out)
