# IntelliFiller - AI Addon for Anki

This is an enhanced version of the [IntelliFiller](https://github.com/ganqqwerty/intellifiller-ai-addon-for-anki) addon for Anki, allowing you to automatically fill note fields using various Large Language Models (LLMs).

> **Tested on Windows 11**

## Features

* **Multi-Provider Support**: Use models from **OpenAI**, **Anthropic**, **Google Gemini**, and **OpenRouter**.
* **Custom Endpoints**: Support for any OpenAI-compatible API (local LLMs, etc.).
* **Configurable Models**: Easily switch between models (e.g., GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro).
* **Batch Processing**: Select multiple cards in the browser and fill them in bulk.
* **Flexible Prompting**: Design prompts that use existing field data (e.g., `{{{Sentence}}}`) to generate new content.
* **Prompt Management**: Save and reuse your favorite prompts.

## Prerequisites

* **Anki** (Latest version recommended)
* **Python 3.9** (For building from source)

## Installation from Source

To install this addon from the source code, follow these steps:

1.  Clone this repository.
2.  Copy the `IntelliFiller` folder into your Anki `addons21` directory.
    *   To find this directory, open Anki, go to **Tools** -> **Add-ons**, click **View Files**.
3.  Install dependencies (see [Build Instructions](#build-instructions)).
4.  Restart Anki.

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

1.  Run `python scripts/build_release.py`.
2.  Zip the contents of the `IntelliFiller` folder.
3.  Rename the `.zip` file to `.ankiaddon`.

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
5.  **Run**: Click **Run** to process the cards.

## Original Project

This project is a fork of [IntelliFiller AI addon for Anki](https://github.com/ganqqwerty/intellifiller-ai-addon-for-anki).
Significant improvements have been made to support a wider range of AI providers and configuration options.

## License

Please refer to the original repository for license information.
