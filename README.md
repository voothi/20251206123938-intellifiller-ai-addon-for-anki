# IntelliFiller AI -  Addon for Anki

This is an enhanced version of the [IntelliFiller](https://github.com/ganqqwerty/intellifiller-ai-addon-for-anki) addon for Anki, allowing you to automatically fill note fields using various Large Language Models (LLMs).

> **Attribution & Source**
>
> This add-on is a modified fork of **IntelliFiller** by ganqqwerty.
>
> *   **Original Project**: [Source Code](https://github.com/ganqqwerty/intellifiller-ai-addon-for-anki) | [AnkiWeb (9559994708)](https://ankiweb.net/shared/info/9559994708)
> *   **This Enhanced Version**: [Source Code](https://github.com/voothi/20251206123938-intellifiller-ai-addon-for-anki) | [AnkiWeb (1149226090)](https://ankiweb.net/shared/info/1149226090)

> [!NOTE]
> **Tested on Windows 11**

[![AnkiWeb](https://img.shields.io/badge/AnkiWeb-1149226090-blue)](https://ankiweb.net/shared/info/1149226090)

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation from Source](#installation-from-source)
- [Updating](#updating)
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

* **Multi-Provider Support**: Use models from **OpenAI**, **Anthropic**, **Google Gemini**, and **OpenRouter**.
* **Custom Endpoints**: Support for any OpenAI-compatible API (local LLMs, etc.).
* **Configurable Models**: Easily switch between models (e.g., GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro).
* **Batch Processing**: Select multiple cards in the browser and fill them in bulk.
* **Flexible Prompting**: Design prompts that use existing field data (e.g., `{{{Sentence}}}`) to generate new content.
* **Prompt Management**: Save and reuse your favorite prompts.

[Return to Top](#table-of-contents)

## Prerequisites

* **Anki** (Latest version recommended)
* **Python 3.9** (For building from source)

[Return to Top](#table-of-contents)

## Installation from Source

To install this addon from the source code, follow these steps:

1.  Clone this repository.
2.  Copy the `IntelliFiller` folder into your Anki `addons21` directory.
    *   To find this directory, open Anki, go to **Tools** -> **Add-ons**, click **View Files**.
3.  Install dependencies (see [Build Instructions](#build-instructions)).
4.  Restart Anki.

![Installation](installation.png)

[Return to Top](#table-of-contents)

## Updating

It is recommended to **backup your data** using the addon's backup feature (Backup tab in settings) before updating.

### Windows Update Instructions

Due to Windows file locking mechanics, updates can fail if the addon is active.

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

Your persistent settings and prompts (in `user_files`) will be preserved.

[Return to Top](#table-of-contents)

## Build Instructions

This project includes scripts to manage Python dependencies (like `openai`, `httpx`) required by the addon.

### For Local Development (Windows 11 / Current OS)

If you are running the addon locally on your machine, run the setup script to install dependencies for your current platform:

```bash
python scripts/setup_vendor.py
```

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

[Return to Top](#table-of-contents)

## Usage

1.  **Open Anki Browser**: Go to the card browser.
2.  **Select Cards**: Select one or more cards you want to fill.

    ![Select Multiple Cards](multiple-cards.png)

3.  **Right-Click**: Choose **IntelliFiller** from the context menu.
4.  **Configure**:
    *   Select your **Provider** (OpenAI, Anthropic, Gemini, etc.).
    *   Enter your **API Key**.
    *   Choose or type the **Model Name**.
    *   Write your prompt using field placeholders like `{{{Front}}}`.
    *   Select the **Destination Field** for the result.

    ![Run Configuration](run-request.png)

    > **Tip**: You can save prompts to reuse them later!
    >
    > ![Save Prompts](save-prompts.png)

5.  **Run**: Click **Run** to process the cards.

### Editor Integration

You can also launch IntelliFiller directly from the note editor:

![Editor Button](editor-button.png)

[Return to Top](#table-of-contents)

## Original Project

This project is a fork of [IntelliFiller AI addon for Anki](https://github.com/ganqqwerty/intellifiller-ai-addon-for-anki) (forked from version 2.1.0).
Significant improvements have been made to support a wider range of AI providers and configuration options.

[Return to Top](#table-of-contents)

## Kardenwort Ecosystem

This project is part of the [Kardenwort](https://github.com/kardenwort) environment, designed to create a focused and efficient learning ecosystem.

[Return to Top](#table-of-contents)

## License

Please refer to the original repository for license information.
