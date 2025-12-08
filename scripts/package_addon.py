import os
import sys
import zipfile
import argparse
from datetime import datetime
from pathlib import Path

# Configuration
EXCLUDED_FILES = {
    "meta.json",
    "credentials.json",
    "settings.json"
}

EXCLUDED_DIRS = {
    "user_files",
    "__pycache__"
}

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
                # Filter exclusions in-place to prevent walking into them
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
                
                for file in files:
                    if file in EXCLUDED_FILES:
                        continue
                        
                    # Calculate relative path for zip structure
                    # We want the content of IntelliFiller to be at root of zip
                    full_path = Path(root) / file
                    relative_path = full_path.relative_to(addon_source_dir)
                    
                    # Double check exclusion for safety (if partial match logic needed in future)
                    if any(part in EXCLUDED_DIRS for part in relative_path.parts):
                        continue

                    zf.write(full_path, arcname=relative_path)
                    
        print(f"✅ Package created successfully!")
        
        # Verify exclusions
        print("🔍 Verifying package content...")
        with zipfile.ZipFile(output_path, 'r') as zf:
            file_list = zf.namelist()
            issues_found = False
            for f in file_list:
                if any(ex in f for ex in EXCLUDED_FILES) or any(ex in f for ex in EXCLUDED_DIRS):
                     print(f"❌ WARNING: Excluded file found in zip: {f}")
                     issues_found = True
            
            if not issues_found:
                print("✅ Verification passed: No sensitive files found.")
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
