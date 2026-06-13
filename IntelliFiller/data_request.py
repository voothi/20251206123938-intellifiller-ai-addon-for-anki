import re
import sys
import os
import json
import urllib.request
import urllib.error


from aqt import mw


import platform
def get_platform_specific_vendor():
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == 'darwin':  # macOS
        if machine == 'arm64':
            return 'darwin_arm64'
        return 'darwin_x86_64'
    elif system == 'windows':
        return 'win32'
    elif system == 'linux':
        return 'linux'
    else:
        raise RuntimeError(f"Unsupported platform: {system} {machine}")

addon_dir = os.path.dirname(os.path.realpath(__file__))
vendor_dir = os.path.join(addon_dir, "vendor", get_platform_specific_vendor())
sys.path.append(vendor_dir)

from .config_manager import ConfigManager

from .anthropic_client import SimpleAnthropicClient
from .gemini_client import GeminiClient
from .ollama_client import OllamaClient
from html import unescape


def _http_chat_completion(url, api_key, model, prompt, timeout=60.0, extra_headers=None):
    """Generic OpenAI-compatible chat completion helper using urllib.

    Returns the assistant message content string.
    Raises Exception on any HTTP/URL error with a descriptive message.
    """
    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if extra_headers:
        headers.update(extra_headers)

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            error_body = str(e)
        raise Exception(f"HTTP {e.code} {e.reason} - {error_body}")
    except urllib.error.URLError as e:
        raise Exception(f"Network error: {str(e)}")
    except KeyError as e:
        raise Exception(f"Unexpected response structure (missing key: {e})")
    except Exception as e:
        raise Exception(f"Request failed: {str(e)}")


def _provider_defaults(config):
    """Resolve the effective API URL, key and model for the selected provider."""
    selected = config.get('selectedApi', 'openai')
    if selected == 'openai':
        return (
            "https://api.openai.com/v1/chat/completions",
            config.get('apiKey', ''),
            config.get('openaiModel') or 'gpt-4o-mini',
            None,
        )
    if selected == 'openrouter':
        return (
            "https://openrouter.ai/api/v1/chat/completions",
            config.get('openrouterKey', ''),
            config.get('openrouterModel') or 'google/gemini-2.0-flash-lite-001',
            {
                "HTTP-Referer": "https://ankiweb.net/",
                "X-Title": "IntelliFiller Anki Addon",
            },
        )
    if selected == 'custom':
        return (
            config.get('customUrl', ''),
            config.get('customKey', ''),
            config.get('customModel') or 'my-model',
            None,
        )
    if selected == 'ollama':
        # Local Ollama is handled separately via OllamaClient.
        return (None, None, None, None)
    if selected == 'ollama_cloud':
        # Ollama Cloud is handled separately via OllamaClient.
        return (None, None, None, None)
    if selected == 'anthropic':
        return (None, None, None, None)
    if selected == 'gemini':
        return (None, None, None, None)
    # Fallback to openai
    return (
        "https://api.openai.com/v1/chat/completions",
        config.get('apiKey', ''),
        config.get('openaiModel') or 'gpt-4o-mini',
        None,
    )


def test_connection(config=None, timeout=15.0):
    """Test API connectivity for the currently selected provider.

    Returns a tuple ``(ok: bool, message: str)``. ``message`` describes either
    success or the failure details.
    """
    try:
        if config is None:
            settings = ConfigManager.load_settings()
            encryption_key = settings.get("encryptionKey", "")
            credentials = ConfigManager.load_credentials(key=encryption_key)
            config = {**settings, **credentials}

        net_timeout = float(config.get("netTimeout", timeout))
        timeout = net_timeout

        selected = config.get('selectedApi', 'openai')

        # Test prompt
        test_prompt = "Reply with the single word: OK"

        if selected == 'anthropic':
            client = SimpleAnthropicClient(
                api_key=config.get('anthropicKey', ''),
                model=config.get('anthropicModel') or 'claude-haiku-4-5',
            )
            resp = client.create_message(test_prompt, max_tokens=20, timeout=timeout)
            return (True, f"Anthropic connection OK. Response: {resp[:60]}")

        if selected == 'gemini':
            client = GeminiClient(
                api_key=config.get('geminiKey', ''),
                model=config.get('geminiModel') or 'gemini-2.0-flash-lite-001',
            )
            resp = client.generate_content(test_prompt, timeout=timeout)
            return (True, f"Gemini connection OK. Response: {resp[:60]}")

        if selected == 'ollama':
            client = OllamaClient(
                api_url=config.get('ollamaUrl') or 'http://localhost:11434/api/generate',
                model=config.get('ollamaModel') or 'llama3',
            )
            resp = client.generate_content(test_prompt, timeout=timeout)
            return (True, f"Ollama connection OK. Response: {resp[:60]}")

        if selected == 'ollama_cloud':
            client = OllamaClient(
                api_url=config.get('ollamaCloudUrl') or 'https://ollama.com/v1',
                api_key=config.get('ollamaCloudKey', ''),
                model=config.get('ollamaCloudModel') or 'llama3',
            )
            resp = client.generate_content(test_prompt, timeout=timeout)
            return (True, f"Ollama Cloud connection OK. Response: {resp[:60]}")

        # OpenAI-compatible providers (openai, openrouter, custom)
        url, api_key, model, extra_headers = _provider_defaults(config)
        if not url:
            return (False, f"Unknown provider: {selected}")

        # Validate required credentials
        if selected == 'openai' and not api_key:
            return (False, "OpenAI API key is missing.")
        if selected == 'openrouter' and not api_key:
            return (False, "OpenRouter API key is missing.")
        if selected == 'custom':
            if not url:
                return (False, "Custom base URL is missing.")

        resp = _http_chat_completion(
            url=url,
            api_key=api_key,
            model=model,
            prompt=test_prompt,
            timeout=timeout,
            extra_headers=extra_headers,
        )
        return (True, f"{selected} connection OK. Response: {resp[:60]}")
    except Exception as e:
        return (False, f"{config.get('selectedApi', 'openai') if config else 'provider'} connection failed: {str(e)}")


def create_prompt(note, prompt_config):
    prompt_template = prompt_config['prompt']
    pattern = re.compile(r'\{\{\{(\w+)\}\}\}')
    field_names = pattern.findall(prompt_template)
    for field_name in field_names:
        if field_name not in note:
            raise ValueError(f"Field '{field_name}' not found in note.")
        prompt_template = prompt_template.replace(f'{{{{{{{field_name}}}}}}}', note[field_name])
    # unescape HTML entities and replace line breaks with spaces
    prompt_template = unescape(prompt_template)
    # remove HTML tags
    prompt_template = re.sub('<.*?>', '', prompt_template)
    return prompt_template


def send_prompt_to_llm(prompt):
    # Load settings first to get encryption key and API selector
    settings = ConfigManager.load_settings()
    encryption_key = settings.get("encryptionKey", "")

    # Load credentials using the key
    credentials = ConfigManager.load_credentials(key=encryption_key)

    # Merge for easier access
    config = {**settings, **credentials}

    # Get timeout from settings (default 10s)
    net_timeout = float(config.get("netTimeout", 10.0))

    if config.get('emulate') == 'yes':
        print("Fake request: ", prompt)
        return f"This is a fake response for emulation mode for the prompt {prompt}."

    try:
        print("Request to API: ", prompt)

        def try_openai_call():
            url = "https://api.openai.com/v1/chat/completions"
            return _http_chat_completion(
                url=url,
                api_key=config.get('apiKey', ''),
                model=config.get('openaiModel') or 'gpt-4o-mini',
                prompt=prompt,
                timeout=net_timeout,
            )

        def try_anthropic_call():
            client = SimpleAnthropicClient(
                api_key=config.get('anthropicKey', ''),
                model=config.get('anthropicModel') or 'claude-haiku-4-5'
            )
            response = client.create_message(prompt, timeout=net_timeout)
            print("Response from Anthropic:", response)
            return response.strip()

        def try_gemini_call():
            client = GeminiClient(
                api_key=config.get('geminiKey', ''),
                model=config.get('geminiModel') or 'gemini-2.0-flash-lite-001'
            )
            response = client.generate_content(prompt, timeout=net_timeout)
            print("Response from Gemini:", response)
            return response.strip()

        def try_openrouter_call():
            return _http_chat_completion(
                url="https://openrouter.ai/api/v1/chat/completions",
                api_key=config.get('openrouterKey', ''),
                model=config.get('openrouterModel') or 'google/gemini-2.0-flash-lite-001',
                prompt=prompt,
                timeout=net_timeout,
                extra_headers={
                    "HTTP-Referer": "https://ankiweb.net/",
                    "X-Title": "IntelliFiller Anki Addon",
                },
            )

        def try_custom_call():
            return _http_chat_completion(
                url=config.get('customUrl', ''),
                api_key=config.get('customKey', ''),
                model=config.get('customModel') or 'my-model',
                prompt=prompt,
                timeout=net_timeout,
            )

        def try_ollama_call():
            client = OllamaClient(
                api_url=config.get('ollamaUrl') or 'http://localhost:11434/api/generate',
                model=config.get('ollamaModel') or 'llama3'
            )
            response = client.generate_content(prompt, timeout=net_timeout)
            print("Response from local Ollama:", response)
            return response.strip()

        def try_ollama_cloud_call():
            client = OllamaClient(
                api_url=config.get('ollamaCloudUrl') or 'https://ollama.com/v1',
                api_key=config.get('ollamaCloudKey', ''),
                model=config.get('ollamaCloudModel') or 'llama3'
            )
            response = client.generate_content(prompt, timeout=net_timeout)
            print("Response from Ollama Cloud:", response)
            return response.strip()

        try:
            if config['selectedApi'] == 'anthropic':
                return try_anthropic_call()
            elif config['selectedApi'] == 'gemini':
                return try_gemini_call()
            elif config['selectedApi'] == 'openrouter':
                return try_openrouter_call()
            elif config['selectedApi'] == 'custom':
                return try_custom_call()
            elif config['selectedApi'] == 'ollama':
                return try_ollama_call()
            elif config['selectedApi'] == 'ollama_cloud':
                return try_ollama_cloud_call()
            else:  # openai
                return try_openai_call()
        except Exception as e:
            raise e
    except Exception as e:
        raise e
