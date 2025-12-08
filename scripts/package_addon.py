import os
import sys
import zipfile
import argparse
from datetime import datetime
from pathlib import Path

# Exclusions configuration
EXCLUDED_ROOT_FILES = {
    "meta.json"
}

EXCLUDED_DIR_NAMES = {
    "user_files",
    "__pycache__",
    ".git",
    ".vscode",
    ".idea"
}

# Recursively sensitive files that should essentially never be in a package 
# regardless of location, unless deep in vendor? 
# Actually, the user's concern is specifically that "settings.json" in vendor MIGHT be needed.
# So we should rely on directory exclusions for sensitive user data.
# The user_files directory is where our sensitive settings.json live.

def create_addon_package(output_dir: str = None):
    # Determine paths
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
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
                # 1. Directory Exclusion (In-place modification)
                # This prevents descending into user_files, __pycache__, etc.
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIR_NAMES]
                
                for file in files:
                    full_path = Path(root) / file
                    relative_path = full_path.relative_to(addon_source_dir)
                    
                    # 2. Specific Root File Exclusions
                    # e.g. meta.json is only excluded if it's in the root
                    if str(relative_path) in EXCLUDED_ROOT_FILES:
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
                for forbidden_dir in EXCLUDED_DIR_NAMES:
                    if f.startswith(f"{forbidden_dir}/") or f == forbidden_dir:
                        print(f"❌ WARNING: Forbidden directory found in zip: {f}")
                        issues_found = True
                
                # Check root files
                if f in EXCLUDED_ROOT_FILES:
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
