# IntelliFiller

## Development Setup
1. Clone the repository
2. Run `python3.9 scripts/setup_vendor.py` to install dependencies for your platform
   - For M1/M2 Mac users: Make sure you're running Python for ARM64
   - For Windows/Intel Mac users: The script will automatically handle your architecture

## Creating a Release
1. Run `python scripts/build_release.py` to build dependencies for all platforms
2. This will create platform-specific directories in the vendor folder:
   - darwin_arm64 (M1/M2 Macs)
   - darwin_x86_64 (Intel Macs)
   - win32 (Windows)
   - linux (Linux)
3. The add-on is now ready to be packaged.

## Packaging for Distribution
Use the included `package_addon.py` script to create a safe `.ankiaddon` artifact that excludes sensitive files (like `user_files`, `meta.json`, `settings.json`, `credentials.json`, `__pycache__`).

```bash
# Default: Creates timestamped .ankiaddon in project root
python scripts/package_addon.py

# Optional: Specify output directory
python scripts/package_addon.py --out "C:/Releases"
```

**Safety Features:**
- Automatically excludes `user_files` directory.
- Excludes root-level sensitive files (`meta.json`, `credentials.json`, `settings.json`).
- Prints a `⚠️ NOTICE` if potentially sensitive files are included from deep subdirectories (e.g. inside `vendor`), allowing you to verify them.

## Troubleshooting
If you encounter architecture-related errors during development:
- M1/M2 Mac users: Ensure you're using the ARM64 version of Python and pip
- Intel Mac users: Use the x86_64 version of Python and pip

## Known conflicts
- the extension can conflict with HyperTTS because of  typing_extensions.py . Disable HyperTTS if you see typing_extensions.py error
- **Windows Update Error:** When updating on Windows, you may encounter `PermissionError`.
  - **Note:** Version v2.14.4+ executes an "Atomic Rename" strategy to avoid this. If you are updating *from* an older version, you may still see this error once.
  - **Prevention:** Disable the addon -> Restart Anki -> Update.
  - **Recovery:** If update failed and addon is named by ID, simply Check for Updates again on that ID -> Update -> Restart Anki.

## Atomic Updates (Technical Details)
The addon works around Windows file locking by hooking into Anki's update process. Instead of deleting the old folder (which fails due to locked `.pyd` files), it **renames** the folder to `_IntelliFiller_trash_TIMESTAMP` (prefixed with `_` so Anki ignores it). These trash folders are automaticall cleaned up on the next Anki startup.
**Do not manually modify `atomic_installer.py` or the update hook in `__init__.py`.**