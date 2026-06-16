# IntelliFiller Release Notes

## Table of Contents

- [v2.24.8](#release-notes-v2248)
- [v2.24.0](#release-notes-v2240)
- [Transition Instructions: Upgrading to v2.24.0 (Windows)](#transition-instructions-upgrading-to-v2240-windows)
- [v2.22.12](#release-notes-v22212)
- [v2.22.2](#release-notes-v2222)
- [v2.20.2](#release-notes-v2202)
- [v2.18.12](#release-notes-v21812)
- [v2.18.10](#release-notes-v21810)
- [v2.18.8](#release-notes-v2188)
- [v2.16.2](#release-notes-v2162)
- [v2.14.12](#release-notes-v21412)
- [v2.14.8](#release-notes-v2148)
- [v2.14.2](#release-notes-v2142)
- [v2.12.2](#release-notes-v2122)
- [v2.6.2](#release-notes-v262)
- [v2.4.12](#release-notes-v2412)
- [v2.4.2](#release-notes-v242)
- [v2.2.4](#release-notes-v224)
- [v2.2.2](#release-notes-v222)

---

## Release Notes v2.24.8

### 🚀 New Features

*   **⚙️ Configurable Max Network Retries**
    *   Added a settings option (`maxNetworkRetries`) to customize the maximum number of network retry attempts (defaulting to `4`).
    *   Supported range from `-1` (finite/disabled endless retry checks) up to `999999` using a flexible SpinBox control in the settings editor.
*   **📋 Tabbed Summary Dialog Enhancements**
    *   **All Failures Tab**: Added a consolidated failures overview tab, displaying all failed notes for convenient selection, copy, and selective retry operations.
    *   **Smart Tab Selection**: Automatically activates the "All Failures" tab when opening the Summary Dialog if errors or failures are present.
    *   **Retry Recovery Tracking**: Displays the number of retries it took for successfully recovered notes.
    *   **Tooltips & Clipboard Copy**: Detailed error logs for each retry attempt are accumulated and shown as tooltips, and can be copied to the clipboard directly using the `Ctrl+C` shortcut in the tables.
*   **📋 Prompt Duplication**
    *   Added a new "Duplicate" button in the Settings window's Prompts tab, allowing users to clone selected prompts instantly and create new ones based on them.
*   **🗣️ Phrase Translation & Prompt Refinement**
    *   Adapted English and German prompts into separate Vocabulary Analysis and Phrase Translation templates.
    *   Reworked the phrase translation prompt templates to automatically fallback to `WordSourceInflectedForm` when `WordSource` is empty, including detailed grammar commentary options.

### 🐛 Bug Fixes & Polish

*   **🖥️ UI Scaling and DPI Compatibility**
    *   Resolved dialog shrinking issues on laptops and high-DPI screens by adding scroll containers for long tabs and adjusting vertical constraints, ensuring the Settings window fits properly without clipping or overlapping the taskbar.
*   **🔇 Reduced Warning Noise**
    *   Redirected native Anki startup/troubleshooting warning messages to standard output instead of standard error, suppressing unwanted popups while retaining useful terminal logs.
*   **🧹 Cleaned Up Prompts**
    *   Removed obsolete templates and cleaned up overall settings files and config schemas.

**Full Changelog**: https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/compare/v2.24.0...v2.24.8

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.24.0

> [!IMPORTANT]
> **Upgrading from v2.22.12 (or older) on Windows?** Please follow the preliminary [Transition Instructions](#transition-instructions-upgrading-to-v2240-windows) to avoid file lock errors during installation.

### 🚀 New Features

*   **🦙 Ollama & Ollama Cloud Integration**
    *   **Local Ollama Support**: Full support for local Ollama deployments (defaulting to `http://localhost:11434/api/generate` and the `llama3` model).
    *   **Ollama Cloud Integration**: Integrated support for Ollama Cloud (defaulting to `https://ollama.com/v1` and requiring an API key).
*   **📊 Tabbed Processing Summary Dialog**
    *   **Granular Categories**: A new tabbed interface (Successful, Skipped, JSON Failures, Network Failures) showing detailed lists of notes processed.
    *   **Retry Selected**: Users can select one or more failed notes inside the summary tabs and trigger a retry execution queue for only the selected items.
    *   *Ported from contribution by [emilythedev](https://github.com/emilythedev/20251206123938-intellifiller-ai-addon-for-anki).*
*   **🧪 Robust Testing Infrastructure**
    *   **Pytest Framework**: Integrated a full pytest architecture under `tests/` with 160+ unit tests covering atomic installers, backup management, LLM providers, and data request logic.
*   **⚙️ Platform & Packaging Enhancements**
    *   **Configurable Python Version**: Added options to target specific Python versions (e.g. `--python-version` defaulting to Python 3.13) for Linux wheel selection during package vendoring, ensuring future-proofing for Anki v25.
    *   *Ported from contribution by [HummerGJB](https://github.com/HummerGJB/intellifiller-ai-addon-for-anki).*

### 🧹 Maintenance & Cleanup

*   **Vendor Clean-up**: Removed redundant external dependencies (`openai` and `httpx` libraries) from the `vendor` folder, relying on standard library `urllib` for OpenAI-compatible and custom endpoints.
*   **Clean Packaging & Build Wrappers**:
    *   Moved release automation scripts into a clean `scripts/packaging/` folder.
    *   Moved hardcoded packaging options, target platforms, exclusions, and pipeline steps to [packaging.ini](file:///u:/voothi/20251206123938-intellifiller-ai-addon-for-anki/scripts/packaging/packaging.ini).
    *   Added a root-level delegator [scripts/make_release.py](file:///u:/voothi/20251206123938-intellifiller-ai-addon-for-anki/scripts/make_release.py) that cleans vendor folders, executes the test suite, and compiles the `.ankiaddon` package dynamically.

**Full Changelog**: https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/compare/v2.22.12...v2.24.0

[Return to Top](#intellifiller-release-notes)

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

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.22.12

### 🚀 New Features

*   **🛡️ Connection Watchdog System**
    *   **Automated Stall Detection**: A new background monitoring system ("Watchdog") now actively supervises network requests. If a connection silently hangs (stops sending data without throwing an error), the interface explicitly warns you with a "Stalled?" message in red.
    *   **Intelligent UI Feedback**: The "Stalled" warning automatically clears and switches to a "Resuming..." state as soon as network activity is detected again, preventing false alarms during active retries.
    
*   **🔌 Enhanced Network Controls**
    *   **Configurable Timeout**: You can now adjust the **Network Timeout** directly in the Settings API tab (default: 10 seconds). This controls how long the system waits for a server response before attempting an automatic retry.
    *   **"Restart" Button**: The "Restart Connection" button has been renamed to **"Restart"** and its logic improved to accurately resume processing from the exact note where it left off, preventing skipped cards or double-counts.

### 🐛 Bug Fixes

*   **Fixed Timeout Defaults**: Resolved an issue where the system could fall back to a hardcoded 60-second timeout even if the configuration was missing. The fallback is now strictly synchronized to **10 seconds** across all modules.
*   **Queue Logic Fixes**: Fixed a bug where waiting/queued windows would incorrectly trigger the "Stalled" warning. The watchdog now correctly ignores tasks that haven't started running yet.
*   **Visual improvements**: The "Stalled" warning color now matches the "Restart" button color for better visual consistency.

### ⚙️ Configuration

*   **Expanded Prompt Library**: Added a new built-in prompt **"English Analysis and Translation (JSON)"**. This complex prompt demonstrates how to analyze English words (Lemma, IPA, Morphology) and translate them into multiple target languages (RU, DE, UA) simultaneously using JSON output mode.

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.22.2

### 🚀 New Features

*   **⏸️ Smart Execution Queue & Pause Control**
    Significant overhaul of the batch processing engine to support managing multiple tasks and granular control:
    *   **Execution Queue**: You can now launch multiple batch operations sequentially. If a task is running, subsequent requests are automatically queued and will start processing as soon as the current one finishes.
    *   **Pause/Resume**: Added a manual **Pause** button to the progress dialog. Pausing a task cleanly stops execution (transactionally after the current note) and yields the execution slot to the next waiting task in the queue.
    *   **Window Title Updates**: The window title now dynamically reflects the queue position (e.g., `Queue: #1`) when waiting.

*   **🖥️ UI Refinements**
    *   **Deck Path Display**: Added a dedicated, read-only field showing the full deck path of the active note.
    *   **Copy Button**: Included a clickable "Copy" icon (page symbol) inside the deck field to instantly copy the full path to the clipboard.
    *   **Responsive Layout**: The progress window is now fully resizeable with a standardized default size.

### 🐛 Bug Fixes

*   **Fixed Race Condition**: Resolved a potential race condition where resuming a paused task could conflict with another active task. The system now correctly re-queues resumed tasks.
*   **PyQt6 Compatibility**: Fixed an `AttributeError` related to icon loading on newer Anki versions using PyQt6.

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.20.2

### 🚀 New Features

*   **🎲 Configurable Random Delay**
    Introduced advanced controls for batch processing:
    *   **Enable Random Delay**: A new toggle allows users to add a layer of jitter to batch pauses.
    *   **Min/Max Random Delay**: Users can now precisely configure the random duration range (in seconds). This helps disperse requests, preventing potential rate limits or synchronization issues during high-volume processing.

### ⚙️ Improvements

*   **⚡ Better Default Batch Settings**
    Updated the default "Batch Processing" configuration to provide a smoother, more efficient experience for most users:
    *   **Batch Size**: 20 notes.
    *   **Fixed Delay**: 5 seconds.
    *   **Random Variance**: 0–10 seconds (enabled by default).

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.18.12

### 🐛 Bug Fixes

*   **Fixed Crash in "Prompts" Submenu**
    Resolved a `NameError` that caused the addon to crash when attempting to run a prompt solely from the "Prompts" submenu context. The missing underlying helper functions have been restored, ensuring reliable launching of prompts from all menu locations (Favorites/History and the nested Submenu).

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.18.10

### ⚙️ Improvements

*   **🔓 Readable Encrypted Backups**
    Refined the logic for password-protected backups. When creating an encrypted archive:
    *   The add-on now **automatically de-obfuscates** your credentials (e.g., API keys) *before* adding them to the archive.
    *   **Security**: Since the ZIP file itself is protected by your chosen password (AES-256), your sensitive data remains secure during transport.
    *   **Portability**: This ensures that once extracted, the `config.json` is human-readable and contains valid keys, allowing for easier manual restoration or migration to a new machine without fighting against internal masking mechanisms.

**Full Changelog**: https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/compare/v2.18.8...v2.18.10

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.18.8

#### **🛡️ Enhanced Backup System**
This release introduces a significant upgrade to the automated backup engine, ensuring your data is even safer:
*   **Recursive User Files Backup:** The backup system now recursively scans the entire `user_files` directory. This means any nested folders, assets, or sub-directories you create within your user files are now fully preserved in backups.
*   **Smart Exclusions:**
    *   **Loop Prevention:** The system intelligently identifies if your backup folder is located *inside* the `user_files` directory and excludes it from the backup process to prevent recursive "backing up of backups."
    *   **Cleaner Archives:** File exclusion logic has been refined to keep backup archives clean of system files like `signatures.json`.
*   **Robust Zip Creation:** The archive generation process has been rewritten to support these recursive structures while maintaining cross-platform compatibility.

#### **⚙️ Configuration & Content**
*   **Expanded Defaults:** The default configuration (`config.json`) has been significantly expanded, likely introducing a robust set of default prompts, presets, or examples to help new users get started immediately.

#### **🧹 Maintenance & Cleanup**
*   **Documentation Refinement:** Removed obsolete developer documentation (`DEVELOPER_README.md`) and consolidated project information into the main [README.md](file:///u:/voothi/20251206123938-intellifiller-ai-addon-for-anki/README.md).
*   **Asset Cleanup:** Removed unused static image assets (`editor-button.png`, `installation.png`, etc.) to reduce the overall package size.
*   **License Update:** Updated the `LICENSE` file.

**Full Changelog**: https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/compare/v2.16.2...v2.18.8

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.16.2

#### **🚀 Enhancements & Refinements**

*   **Smart Batch Processing with Countdown:**
    *   Added a visual countdown timer to the progress dialog during batch processing pauses. Users can now see exactly how many seconds remain before the next batch begins.
    *   **Live Browser Refresh:** The Anki Browser list now automatically refreshes during these batch pauses, allowing users to verify generated content incrementally without waiting for the entire queue to finish.

*   **Improved Error Management:**
    *   **Reduced Error Noise:** Implemented a new error suppression logic. The native Anki error dialog will now appear **only once** for the first error encountered during a batch operation. Subsequent errors (e.g., network timeouts) are handled silently or skipped, preventing the user from being flooded with pop-ups and allowing the rest of the batch to proceed smoothly.

*   **Robust Cancellation & UI Logic:**
    *   **Graceful Dialog Closing:** Overhauled the Progress Dialog's closing behavior. Pressing **Esc** or clicking the **'X'** button now properly triggers the cancellation routine—stopping the worker thread and executing cleanup—rather than just hiding the window.
    *   **Guaranteed State Reset:** Improved cleanup logic to ensure the Anki Browser is always reset (reloading the note list) upon cancellation, preventing any "stuck" UI states or partial updates from being hidden.

*   **Network Resilience for Batching:**
    *   Refined the retry logic for network-related errors (timeouts, connection issues) within the worker thread to better cooperate with the new cancellation and error damping features.

**Full Changelog**: https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/compare/v2.14.12...v2.16.2

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.14.12

### 🎨 User Interface Improvements
*   **Prompts Tab Overhaul**: The **Prompts** tab in the Settings window has been completely redesigned to match the *Master-Detail* layout of the Pipelines tab.
    *   **Unified Design**: A list of prompts is now displayed on the left, with editable details on the right.
    *   **Improved Management**: Adding, removing, and editing prompts is now much faster and easier, especially for users with many saved prompts.
*   **Standardized Settings Dialog**: The Settings window now features standard **OK**, **Cancel**, and **Save** (Apply) buttons, aligning with native OS dialog behaviors.

### ⚡ Usability Enhancements
*   **Smart Change Detection**: The Settings window now intelligently tracks your edits.
    *   If you close the window (via `Esc` or 'X') without making changes, it closes immediately.
    *   The "Unsaved Changes" warning now **only** appears if you have actually modified a setting.
*   **Reduced Error Noise**: Fixed an issue where connection errors during batch processing would flood the screen with popups. The system now limits error reporting to a single notification per batch operation.

### 🛡️ Security & Build
*   **Packaging Upgrades**: Enhanced the build scripts to strictly enforce the exclusion of sensitive development files (such as `meta.json` or local `credentials.json`) from the final `.ankiaddon` package.

**Full Changelog**: https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/compare/v2.14.8...v2.14.12

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.14.8

### 🚀 Key Improvements

#### 🛠️ Robust Windows Updates (Atomic Rename)
We have completely rewritten the update mechanism for Windows users to prevent the dreaded `PermissionError: [WinError 5] Access is denied`. 
- **The Fix:** Instead of trying to delete locked files (like `.pyd` dependencies) during an update, the addon now "atomically renames" the old version to a temporary trash folder and "neutralizes" it.
- **Auto-Cleanup:** These trash folders are automatically cleaned up silently the next time you start Anki.
- **No More Errors:** This ensures future updates proceed smoothly without requiring you to manually disable the addon or restart Anki beforehand.

#### 📦 New Packaging Tools (For Developers)
Added a specialized packaging utility to safe-guard releases:
- `scripts/package_addon.py`: Creates clean `.ankiaddon` builds.
- Automatically excludes sensitive user data (`user_files`, `credentials.json`, `settings.json`) and development artifacts (`__pycache__`).
- Includes warnings if potentially sensitive files are detected in `vendor`.

### 🐛 Bug Fixes
- **Fixed Startup Crash:** Resolved a `NameError: name 'Path' is not defined` that could occur on initialization.
- **Fixed "Add-on Startup Failed"**: Corrected an issue where Anki attempted to load "trash" folders from previous updates. We now immediately remove `__init__.py` and `manifest.json` from the old folder during the rename process, so Anki correctly ignores it.

**Full Changelog**: https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/compare/v2.14.2...v2.14.8

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.14.2

### 🛡️ Backup & Security

*   **🔐 Encrypted Backups**
    Implemented robust **AES-256 encryption** for backup archives to ensure maximum user data security.

*   **🕰️ Smart Retention Policies**
    Added configurable retention settings, allowing users to define exactly how many **hourly**, **daily**, **monthly**, and **yearly** backups to keep.

*   **⏱️ Custom Backup Intervals**
    Users can now set specific time intervals (in minutes) for automated backups and toggle the "Backup on Settings Open" behavior.

### 🐛 Bug Fixes & Improvements

*   **🐧 Cross-Platform Build Fixes**
    Resolved critical issues with dependency packaging (specifically `pyzipper`) on non-Windows platforms, ensuring smoother cross-platform builds.

*   **📦 Vendor Dependency Management**
    Improved `scripts/setup_vendor.py` and `scripts/build_release.py` to ensure correct installation and compatibility of required libraries across different operating systems.

*   **🧱 Stability**
    General improvements to the **backup manager logic** to handle edge cases better and ensure reliable execution.

**Full Changelog**: https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/compare/v2.12.2...v2.14.2

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.12.2

### 🚀 New Features & Enhancements

*   **🔌 Expanded LLM Provider Support**
    Added full support for **OpenRouter** and **Custom (OpenAI-compatible)** providers, extending the existing integration options.

*   **🛠️ Granular Model Configuration**
    Users can now specify distinct model names for every provider (**OpenAI**, **Anthropic**, **Gemini**, **OpenRouter**, **Custom**) independently within the settings.

*   **⚡ Multi-Field Updates**
    Introduced a **JSON response format** option for prompts. This allows a single AI response to update multiple Anki fields simultaneously based on a configurable field mapping.

### 🔒 Security & UI

*   **🛡️ Security & Obfuscation**
    Added a toggle to **obfuscate sensitive credentials** in `credentials.json` along with support for a custom encryption key, preventing API keys from being stored in plain text.

*   **🖥️ UI Modernization**
    Updated the settings interface to accommodate new provider options, model fields, and security controls, including visual indicators for the obfuscation state.

**Full Changelog**: https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/compare/v2.8.2...v2.12.2

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.6.2

### 🏗 Architecture & Core Logic
*   **Pipeline Architecture**: Introduced a new **Pipelines** concept in the configuration schema. This logic allows users to define complex workflows (chains of prompts) rather than just single prompt executions.
*   **History Management**: Implemented a state tracking system (`History Management`) to keep logs of processed notes, likely preventing redundant generations or allowing rollbacks.
*   **Concurrency Model**: Added threaded processing logic for **multi-note operations**. The backend now handles batch requests asynchronously to prevent the Anki UI from freezing during large tasks.

### 💻 UI Components
*   **Progress Dialog**: Implemented a dedicated `ProgressDialog` class that visualizes the status of batch operations (e.g., "Processing 5/20 notes") with cancellation support.
*   **Context Menu Integration**: Added event handlers to inject "Generate" options into both the **Browser** context menu (for batch selections) and the **Editor** toolbar (for single notes).

### ⚙️ Configuration
*   **Schema Validation**: Enhanced the settings backend to strictly validate the new "Pipeline" structures and API configurations before saving.

**Full Changelog**: [v2.4.12...v2.6.2](https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/compare/v2.4.12...v2.6.2)

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.4.12

### 💻 Codebase Changes
*   **Settings Dialog Implementation**: Introduced a new `SettingsDialog` class using the Qt framework. This creates a dedicated UI layer for configuration, decoupling user settings from manual file edits.
*   **Dynamic Configuration Backend**: Refactored the `config` module to support runtime updates. Changes to **API Keys** and **Model Providers** (OpenAI, Anthropic, Gemini) are now immediately serialized and applied without requiring an Anki restart.
*   **Prompt Management Logic**: Implemented the CRUD (Create, Read, Update, Delete) logic for custom prompts directly within the UI. The backend now dynamically handles prompt definitions, allowing for safer and more flexible prompt engineering.
*   **Manifest Update**: Updated `manifest.json` to reflect the new version and package structure.

**Full Changelog**: [v2.4.2...v2.4.12](https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/compare/v2.4.2...v2.4.12)

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.4.2

### 🚀 New Features
*   **Core Note Processing**: Implemented the primary logic for processing Anki notes with AI, enabling the core functionality of the addon.
*   **UI & Configuration**: Added essential UI components and configurable settings, allowing users to interact with and customize the addon's behavior more effectively.

### 🔧 Internal Changes
*   **Manifest Update**: Updated `manifest.json` to include the correct addon name, package ID, and version information, ensuring proper recognition and installation within Anki.

**Full Changelog**: [v2.2.4...v2.4.2](https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/compare/v2.2.4...v2.4.2)

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.2.4

### 🐛 Bug Fixes
*   **Fix "Add Prompt" Button**: Resolved an issue in the Settings Editor where the **"Add Prompt"** button was not functioning correctly. You can now successfully add and configure new custom prompts directly through the user interface.

### 🔧 Internal Changes
*   **Manifest Update**: Updated `manifest.json` to strictly define the addon name (**IntelliFiller AI Anki Addon**) and package details, ensuring correct recognition within Anki.

**Full Changelog**: [v2.2.2...v2.2.4](https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki/compare/v2.2.2...v2.2.4)

[Return to Top](#intellifiller-release-notes)

## Release Notes v2.2.2

### 🚀 New Features
*   **Multi-Provider Support**: added full integration for **OpenAI**, **Anthropic**, and **Google Gemini** LLMs. You can now choose your preferred AI provider and configure API keys directly within the addon.
*   **Advanced Settings UI**: Introduced a new Settings window with dedicated tabs for **API Configuration** and **Prompt Management**, making it easier to manage models and custom prompts.
*   **Batch Processing**: Added support for processing **multiple notes** at once in the Anki browser. A new progress dialog now displays the status of batch operations.
*   **Run Prompt Dialog**: Implemented a new `RunPromptDialog` that allows you to edit and execute prompts on the fly with built-in field validation.
*   **Editor Integration**: Added a dedicated button in the Editor and a context menu in the Browser for quick access to AI generation tools.

### ⚙️ Improvements
*   **Prompt Validation**: Improved logic to validate fields before running prompts, ensuring smoother execution.
*   **Cross-Platform Support**: Added scripts for cross-platform vendoring of Python dependencies to ensure compatibility across different operating systems.
*   **Modular Backend**: Refactored the backend with a new `data_request` module to handle requests efficiently across different AI providers (OpenAI, Anthropic, Gemini).

### 📖 Documentation
*   **Enhanced README**: Significantly updated the documentation with a Table of Contents, navigation links, and detailed guides.
*   **New Visuals**: Added screenshots and step-by-step instructions for Editor integration, multi-provider setup, and custom endpoint configuration.

[Return to Top](#intellifiller-release-notes)