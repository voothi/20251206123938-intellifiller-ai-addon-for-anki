# IntelliFiller AI - Multi-Provider Prompt Orchestrator

[![Version](https://img.shields.io/badge/version-v2.18.2-blue)](https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/releases) 
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 
[![AnkiWeb](https://img.shields.io/badge/AnkiWeb-1149226090-blue)](https://ankiweb.net/shared/info/1149226090)

This is an enhanced version of the [IntelliFiller](https://github.com/ganqqwerty/intellifiller-ai-addon-for-anki) addon for Anki, allowing you to automatically fill note fields using various Large Language Models (LLMs).

For a detailed history of changes, please view the [Releases Page](https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/releases).

> **Attribution & Source**
>
> This add-on is a modified fork of **IntelliFiller** by ganqqwerty.
>
> *   **Original Project**: [Source Code](https://github.com/ganqqwerty/intellifiller-ai-addon-for-anki) | [AnkiWeb (9559994708)](https://ankiweb.net/shared/info/9559994708) | [AnkiWeb (1416178071)](https://ankiweb.net/shared/info/1416178071) | [Anki Forums (31618)](https://forums.ankiweb.net/t/intellifiller-chatgpt-addon/31618)
> *   **This Enhanced Version**: [Source Code](https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki) | [AnkiWeb (1149226090)](https://ankiweb.net/shared/info/1149226090)

> [!NOTE]
> **Cross-Platform Ready (Linux & macOS)**
>
> **Developed & Validated Environment:**
> *   **OS**: Windows 11 (Python 3.9.13 via Microsoft Store)
> *   **Anki**: Version 24.06.3 (d678e393) - (Python 3.9.18 / Qt 6.6.2 / PyQt 6.6.1)


## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Updating](#updating)
- [Advanced / Developer Installation](#advanced--developer-installation)
- [Build Instructions](#build-instructions)
  - [For Local Development (Windows 11 / Current OS)](#for-local-development-windows-11--current-os)
  - [For Cross-Platform Release](#for-cross-platform-release)
  - [Packaging](#packaging)
- [Usage](#usage)
- [Original Project](#original-project)
- [Kardenwort Ecosystem](#kardenwort-ecosystem)
- [License](#license)

---

## Features

* **Multi-Provider Support**: Use models from **OpenAI**, **Anthropic**, **Google Gemini**, **OpenRouter**, and **Ollama**.
* **Custom Endpoints**: Support for any OpenAI-compatible API (local LLMs, etc.).
* **Configurable Models**: Easily switch between models (e.g., GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro).
* **Smart Batch Processing**: 
    *   **Batch Processing**: Select multiple cards in the browser and fill them in bulk.
    *   **Configurable Delays**: Set delays between requests to avoid rate limits.
    *   **Progress Tracking**: Real-time progress dialog with pause/resume capabilities.
* **Flexible Prompting**: 
    *   Design prompts that use existing field data (e.g., `{{{Sentence}}}`) to generate new content.
    *   **Multi-Field Updates**: Support for JSON responses to update multiple fields from a single prompt.
* **Advanced Prompt Management**: 
    *   **Master-Detail Interface**: Manage your prompts with an intuitive split-view editor.
    *   **Save & Reuse**: Store your favorite prompts for quick access.
* **Secure Backups**: Automatic, encrypted backups of your settings and prompts.

[Return to Top](#table-of-contents)

## Prerequisites

* **Anki** (Latest version recommended)
* **Python 3.9** (For building from source)

[Return to Top](#table-of-contents)

## Installation

### Method 1: AnkiWeb (Recommended)

1.  Open Anki.
2.  Go to **Tools** -> **Add-ons**.
3.  Click **Get Add-ons...**
4.  Enter the code: `1149226090`
5.  Restart Anki.

### Method 2: Manual Installation (Release File)

1.  Download the latest `.ankiaddon` file from the [Releases Page](https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/releases).
2.  Open Anki.
3.  Go to **Tools** -> **Add-ons**.
4.  Click **Install from file...**
5.  Select the downloaded `.ankiaddon` file.
6.  Restart Anki.

[Return to Top](#table-of-contents)

## Advanced / Developer Installation

To install this addon from the source code (for development purposes), follow these steps:

1.  Clone this repository.
2.  Copy the `IntelliFiller` folder into your Anki `addons21` directory.
    *   To find this directory, open Anki, go to **Tools** -> **Add-ons**, click **View Files**.
3.  Install dependencies (see [Build Instructions](#build-instructions)).
4.  Restart Anki.

[Return to Top](#table-of-contents)

## Updating

It is recommended to **backup your data** using the addon's backup feature (Backup tab in settings) before updating.
**If the "Backups" tab is not available in your current version**, please manually copy the entire addon folder from your `addons21` directory to a safe location before proceeding.

### Updating via .ankiaddon File
1.  Download the new `.ankiaddon` file from Releases.
2.  Install it using **Install from file...** in Anki's Add-on menu. This will overwrite the old version while preserving your user files.

### Windows Update Instructions
**Note:** Versions **v2.14.8+** include an automatic "Atomic Update" mechanism to prevent file locking errors. Future updates should proceed smoothly.

If you are updating **from** an older version (< v2.14.8), or if you encounter a `PermissionError`:

**Method 1: Smooth Update (Recommended)**
1.  Go to **Tools** -> **Add-ons**.
2.  Select `IntelliFiller` and toggle it to **Disabled**.
3.  **Restart Anki**.
4.  Check for updates and install the update.
5.  Enable the addon and **Restart Anki**.

**Method 2: Recovering from a Failed Update**
If you tried to update without disabling and received an error (and the addon now appears as a number like `1149226090`):
1.  Select the numbered addon entry (e.g. `1149226090`).
2.  Click **Check for Updates** again and confirm the update.
3.  Once finished, **Restart Anki**. The addon should work correctly and the name will be restored.

### Technical Note: Atomic Updates
The addon works around Windows file locking by hooking into Anki's update process. Instead of deleting the old folder, it **renames** it to `_IntelliFiller_trash_TIMESTAMP` and **immediately deletes** `__init__.py` and `manifest.json` from it. This prevents Anki from loading the trash folder on startup while ensuring the locked binary files can be cleaned up later.

Your persistent settings and prompts (in `user_files`) will be preserved.

[Return to Top](#table-of-contents)

## Build Instructions

This project includes scripts to manage Python dependencies (like `openai`, `httpx`) required by the addon.

### For Local Development (Windows 11 / Current OS)

If you are running the addon locally on your machine, run the setup script to install dependencies for your current platform:

```bash
python scripts/setup_vendor.py
```
*   **Mac M1/M2 Users**: Ensure you are running the ARM64 version of Python.
*   **Windows/Intel Mac**: The script automatically handles your architecture.

This will populate the `IntelliFiller/vendor` directory with the necessary libraries.

### For Cross-Platform Release

To build a release that supports multiple platforms (Windows, macOS ARM/Intel, Linux), use the build release script:

```bash
python scripts/build_release.py
```

This creates a `vendor` directory with subfolders for each platform, ensuring the addon works regardless of the user's OS.

### Packaging

To create an `.ankiaddon` package for distribution:

1.  Run `python scripts/build_release.py` to prepare dependencies.
2.  Run `python scripts/package_addon.py` to create the artifact.

This will generate a timestamped `.ankiaddon` file in the project root, safely excluding sensitive user files.
You can optionally specify an output directory:
```bash
python scripts/package_addon.py --out "C:/My/Builds"
```

**Packaging Safety Features:**
*   Automatically excludes sensitive user files (`user_files` directory).
*   Excludes root-level secrets (`meta.json`, `credentials.json`, `settings.json`).
*   Prints a warning if potentially sensitive files are detected in deep subdirectories.

[Return to Top](#table-of-contents)

## Usage

1.  **Open Anki Browser**: Go to the card browser.
2.  **Select Cards**: Select one or more cards you want to fill.
3.  **Right-Click**: Choose **IntelliFiller** from the context menu.
4.  **Configure**:
    *   Select your **Provider** (OpenAI, Anthropic, Gemini, etc.).
    *   Enter your **API Key**.
    *   Choose or type the **Model Name**.
    *   Write your prompt using field placeholders like `{{{Front}}}`.
    *   Select the **Destination Field** for the result.
    *   *(Optional)* Use the **Prompts** tab to save or load existing prompt configurations.
5.  **Run**: Click **Run** to process the cards.

### Editor Integration

You can also launch IntelliFiller directly from the note editor using the dedicated button in the editor toolbar.

[Return to Top](#table-of-contents)

## Troubleshooting & Known Issues

### Known Conflicts
*   **HyperTTS**: This extension may conflict with HyperTTS due to shared dependencies (`typing_extensions.py`). If you see errors related to this, try disabling HyperTTS temporarily.

### Architecture Errors
*   **M1/M2 Mac Users**: Ensure you are using the **ARM64** version of Python and pip when building from source.
*   **Intel Mac Users**: Use the **x86_64** version.

[Return to Top](#table-of-contents)

## Original Project

This project is a fork of [IntelliFiller AI addon for Anki](https://github.com/ganqqwerty/intellifiller-ai-addon-for-anki) (forked from version 2.1.0).
Significant improvements have been made to support a wider range of AI providers and configuration options.

[Return to Top](#table-of-contents)

## Kardenwort Ecosystem

This project is part of the [Kardenwort](https://github.com/kardenwort) environment, designed to create a focused and efficient learning ecosystem.

[Return to Top](#table-of-contents)

## License

This project is licensed under the **MIT License**.

See the [LICENSE](LICENSE) file for details.
