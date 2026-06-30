import os
import sys
import subprocess
import argparse

SHORTCUT_DISPLAY_NAME = "IntelliFiller Fill"
SENDTO_DIRECTORY = r"%APPDATA%\Microsoft\Windows\SendTo"

def create_shortcut(name, prompt_name):
    sendto_dir = os.path.expandvars(SENDTO_DIRECTORY)
    os.makedirs(sendto_dir, exist_ok=True)
    shortcut_path = os.path.join(sendto_dir, f"{name}.lnk")

    python_path = sys.executable
    if python_path.lower().endswith("pythonw.exe"):
        python_path = python_path[:-len("pythonw.exe")] + "python.exe"

    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "IntelliFiller", "headless_entrypoint.py")

    shortcut_path_escaped = shortcut_path.replace("'", "''")
    python_path_escaped = python_path.replace("'", "''")
    script_path_escaped = script_path.replace("'", "''")

    # Windows automatically appends the target file path to the arguments.
    # So by ending arguments with --tsv, it will form:
    # --prompt "<prompt_name>" --tsv "<selected_file_path>"
    arguments = f'"{script_path_escaped}" --prompt "{prompt_name}" --tsv'

    ps_script = (
        f"$WshShell = New-Object -ComObject WScript.Shell; "
        f"$Shortcut = $WshShell.CreateShortcut('{shortcut_path_escaped}'); "
        f"$Shortcut.TargetPath = '{python_path_escaped}'; "
        f"$Shortcut.Arguments = '{arguments}'; "
        f"$Shortcut.Description = 'Run headless IntelliFiller on the selected TSV'; "
        f"$Shortcut.WindowStyle = 1; "   # SW_SHOWNORMAL
        f"$Shortcut.Save()"
    )

    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"SUCCESS: Created SendTo shortcut '{name}'")
    except subprocess.CalledProcessError as exc:
        print(f"Error: Failed to create shortcut '{name}'.\nPowerShell error:\n{exc.stderr}")

def main():
    parser = argparse.ArgumentParser(description="IntelliFiller SendTo Shortcut Installer")
    parser.add_argument("--list", action="store_true", help="List all registered shortcuts")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall the registered shortcut")
    args = parser.parse_args()

    if args.list:
        print("Registered SendTo entrypoints:")
        print(f"  - {SHORTCUT_DISPLAY_NAME}: Fills TSV with English Vocabulary Analysis and Translation prompt")
        return

    if args.uninstall:
        sendto_dir = os.path.expandvars(SENDTO_DIRECTORY)
        shortcut_path = os.path.join(sendto_dir, f"{SHORTCUT_DISPLAY_NAME}.lnk")
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            print(f"Removed shortcut '{SHORTCUT_DISPLAY_NAME}'")
        return

    print("Installing IntelliFiller shortcuts...")
    create_shortcut(SHORTCUT_DISPLAY_NAME, "English Vocabulary Analysis and Translation (JSON)")

if __name__ == "__main__":
    main()
