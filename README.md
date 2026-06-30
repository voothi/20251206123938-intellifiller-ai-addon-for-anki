# IntelliFiller AI - Multi-Provider Prompt Orchestrator

[![Version](https://img.shields.io/badge/version-v2.24.8-blue)](https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/releases) 
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 
[![AnkiWeb](https://img.shields.io/badge/AnkiWeb-1149226090-blue)](https://ankiweb.net/shared/info/1149226090)

This is an enhanced version of the [IntelliFiller](https://github.com/ganqqwerty/intellifiller-ai-addon-for-anki) addon for Anki, allowing you to automatically fill note fields using various Large Language Models (LLMs).

For a detailed history of changes, please view the [release-notes.md](release-notes.md) file or the [Releases Page](https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/releases).

> [!IMPORTANT]
> **Upgrading from v2.22.12 (or older) on Windows?** Please follow the preliminary [Transition Instructions](#transition-instructions-upgrading-to-v2240-windows) to avoid file lock errors during installation.

> **Attribution & Source**
>
> This add-on is a modified fork of **IntelliFiller** by ganqqwerty.
>
> *   **Original Project**: [Source Code](https://github.com/ganqqwerty/intellifiller-ai-addon-for-anki) | [AnkiWeb (9559994708)](https://ankiweb.net/shared/info/9559994708) | [AnkiWeb (1416178071)](https://ankiweb.net/shared/info/1416178071) | [Anki Forums (31618)](https://forums.ankiweb.net/t/intellifiller-chatgpt-addon/31618)
> *   **This Enhanced Version**: [Source Code](https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki) | [AnkiWeb (1149226090)](https://ankiweb.net/shared/info/1149226090)

> [!NOTE]
> **Cross-Platform Ready (Linux & macOS)**
>
> **Developed & Validated Environments:**
> *   **Anki-Current**
>     *   **OS**: Windows 11 (Python 3.9.13 via Microsoft Store)
>     *   **Anki**: Version 24.06.3 (d678e393) - (Python 3.9.18 / Qt 6.6.2 / PyQt 6.6.1)
> *   **Anki-Next (Anki 25 Support)**
>     *   **OS**: Windows 11 (Python 3.13.0 from official installer)
>     *   **Anki**: Version 25.09.4 (d52ca669) - (Python 3.13.5 / Qt 6.9.1 / Chromium 122)


## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Updating](#updating)
- [Transition Instructions: Upgrading to v2.24.0 (Windows)](#transition-instructions-upgrading-to-v2240-windows)
- [Advanced / Developer Installation](#advanced--developer-installation)
- [Build Instructions](#build-instructions)
  - [For Local Development (Windows 11 / Current OS)](#for-local-development-windows-11--current-os)
  - [For Cross-Platform Release](#for-cross-platform-release)
  - [Packaging](#packaging)
- [Usage](#usage)
- [Headless Mode (CLI)](#headless-mode-cli)
- [Testing](#testing)
- [Configuration Guide](#configuration-guide)
- [Original Project](#original-project)
- [Kardenwort Ecosystem](#kardenwort-ecosystem)
- [License](#license)

---

## Features

* **Multi-Provider Support**: Use models from **OpenAI**, **Anthropic**, **Google Gemini**, **OpenRouter**, **Ollama**, and **Ollama Cloud**.
* **Custom Endpoints**: Support for any OpenAI-compatible API (local LLMs, etc.).
* **Configurable Models**: Easily switch between models (e.g., GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro).
* **Smart Batch Processing**: 
    *   **Batch Processing**: Select multiple cards in the browser and fill them in bulk.
    *   **Configurable Delays**: Set fixed and **random** delays between batches to avoid rate limits and disperse requests.
    *   **Execution Queue**: Queue multiple batch tasks to run sequentially.
    *   **Pause/Resume**: Manually pause processing to inspect results or yield to other tasks.
    *   **Progress Tracking**: Real-time progress dialog with live countdown, pause/resume, and copyable deck path.
    *   **Connection Watchdog**: Actively monitors connection requests and alerts users if a request stalls or hangs.
    *   **Failures Summary Dialog**: Tabbed overview (Successful, Skipped, JSON Failures, Network Failures) showing notes status.
    *   **Selective Retry**: Rerun only the highlighted notes from the failure tabs directly without reprocessing the whole batch.
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

## Transition Instructions: Upgrading to v2.24.0 (Windows)

If you are upgrading from **v2.22.12 (or older)** to **v2.24.0** on Windows, you will likely encounter a `PermissionError: [WinError 5] Access is denied` on `_Salsa20.pyd` because the old version imported `pyzipper` at startup, locking the binary files.

To complete the upgrade, you must perform these preliminary steps to release the locks:

### Method 1: Via Anki's UI (Recommended)
1. In Anki, go to **Tools** -> **Add-ons**.
2. Select **IntelliFiller** and click **Toggle Enabled** (disabling the addon).
3. **Restart Anki** (this starts Anki without loading the addon, releasing all file locks).
4. Go to **Tools** -> **Add-ons**, click **Install from file...**, and select the new `v2.24.0` `.ankiaddon` file.
5. Select **IntelliFiller**, click **Toggle Enabled** (re-enabling it), and **Restart Anki** once more.

### Method 2: Manual Update
1. **Close Anki** completely.
2. Open Windows Explorer or PowerShell and navigate to your Anki addons directory:
   `C:\Users\voothi\AppData\Roaming\Anki2\addons21\`
3. **Delete** the entire `1149226090` folder.
4. **Start Anki** and install the new `v2.24.0` `.ankiaddon` file.

> [!NOTE]
> Once you have upgraded to **v2.24.0**, all future updates (e.g. to `v2.24.1`+) will update automatically and seamlessly without needing these steps because the new version does not load native binaries on startup.

[Return to Top](#table-of-contents)

## Build Instructions

This project includes structured packaging scripts to manage Python dependencies required by the addon and build distributable releases. All configuration parameters, exclusions, and pipeline steps are defined in [packaging.ini](file:///u:/voothi/20251206123938-intellifiller-ai-addon-for-anki/scripts/packaging/packaging.ini).

### Unified Release Pipeline (Recommended)

To run a complete clean build (which automatically sets up local vendor packages, executes the pytest suite, and compiles the `.ankiaddon` archive), run:

```bash
python scripts/make_release.py
```

### Manual Packaging Steps

If you want to perform individual steps manually, the following scripts are available in the [scripts/packaging/](file:///u:/voothi/20251206123938-intellifiller-ai-addon-for-anki/scripts/packaging/) directory:

#### 1. Setup Local Vendor
To setup the `IntelliFiller/vendor` directory for your current OS and architecture (cleaning any old or deprecated packages):
```bash
python scripts/packaging/setup_local_vendor.py
```

#### 2. Pre-Build Vendor for All Platforms
To fetch and pre-build binary wheels for all target deployment platforms (Windows, macOS ARM/Intel, Linux):
```bash
python scripts/packaging/build_all_vendors.py
```

#### 3. Create Addon ZIP
To package the compiled addon assets into an `.ankiaddon` file manually:
```bash
python scripts/packaging/create_addon_zip.py
```
You can optionally specify a custom output directory:
```bash
python scripts/packaging/create_addon_zip.py --out "C:/My/Builds"
```

**Packaging Safety Features:**
*   Automatically excludes sensitive user files (`user_files` directory).
*   Excludes secrets (`meta.json`, `credentials.json`, `settings.json`).
*   Logs warnings if potentially sensitive files are detected in deep vendor subfolders.

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

## Headless Mode (CLI)

IntelliFiller can run headlessly from the command line on any vocabulary TSV file without launching Anki.

### Installation
To install the SendTo shortcut for headless mode, run the installer:
```bash
python install.py
```
This will register the **IntelliFiller Fill** shortcut in your Windows "Send to" menu.

### Command Line Interface
You can call the headless entrypoint directly:
```bash
python IntelliFiller/headless_entrypoint.py --tsv "[tsv_path]" --prompt "[prompt_name]" [--field-mapping "[json_mapping]"]
```

- **Arguments**:
  - `--tsv`: Absolute or relative path to the `.tsv` file containing your vocabulary data.
  - `--prompt`: Name of the prompt to apply (e.g., `English Vocabulary Analysis and Translation (JSON)`).
  - `--field-mapping`: (Optional) JSON string mapping JSON response keys to TSV column headers (e.g., `{"ru": "WordDestination"}`).

- **Behavior**:
  - Automatically loads settings and prompts from the local `user_files/` directory.
  - Resolves placeholders like `{{{WordSource}}}` from TSV column values for each row.
  - Invokes the configured LLM API (OpenAI, Anthropic, Gemini, Ollama, etc.).
  - Writes back the filled columns atomically (preserving other fields).

[Return to Top](#table-of-contents)

## Testing

The project includes a unified `pytest` suite for offline testing of core configurations, API client payload structures, and settings editor UI mapping.

### Setup Test Environment

Before running the tests, install the test dependencies from the root directory:

```bash
pip install -r tests/requirements.txt
```

### Running Tests

Execute `pytest` from the **project root**:

*   **Run all tests**:
    ```bash
    python -m pytest
    ```
*   **Run only unit tests**:
    ```bash
    python -m pytest tests/unit/
    ```

### Mocking Details

To allow tests to run offline without a running Anki desktop instance or PyQt GUI loop:
*   **Anki/Qt Mocks**: [tests/conftest.py](file:///u:/voothi/20251206123938-intellifiller-ai-addon-for-anki/tests/conftest.py) mocks `aqt`, `anki`, and PyQt elements pre-emptively.
*   **Pyzipper & Cryptodome Mocks**: Prevents loading native binaries in the third-party `vendor` directory that might mismatch system Python architectures.
*   **Isolated Config**: An autouse fixture isolates all `ConfigManager` load/save operations to a temporary directory per-test, avoiding any pollution of developer/user configuration files.

[Return to Top](#table-of-contents)

## Configuration Guide

For advanced users who prefer editing JSON files or need to understand the underlying keys, here is an explanation of the configuration parameters.

### Keys Explanation

- `apiKey`: Your personal OpenAI GPT API key.
- `emulate`: Set to "yes" to use fake responses for testing, "no" for real API requests.

### Prompt Configuration

The `prompts` section is a list of prompt objects. Each object contains:

- `prompt`: The text template sent to the AI.
  
  **Using Placeholders:**
  The `prompt` field can contain placeholders in the form of `{{{field_name}}}`. Each `field_name` must correspond to a field in your Anki notes.
  
  *Example:*
  > If you have a note with a "Word" field containing "apple", using `{{{Word}}}` in your prompt will replace it with "apple".
  >
  > Prompt: "Explain the usage of {{{Word}}} in a sentence."
  > Sent to AI: "Explain the usage of apple in a sentence."

- `targetField`: The field name where the API response will be stored.
- `promptName`: A descriptive name for this prompt shown in the UI.

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
