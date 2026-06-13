import pytest
import httpx
import openai
from IntelliFiller.anthropic_client import SimpleAnthropicClient
from IntelliFiller.gemini_client import GeminiClient
from IntelliFiller.config_manager import ConfigManager
from IntelliFiller import data_request

def test_anthropic_client(mocker):
    mock_post = mocker.patch("httpx.post")
    
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "content": [{"text": "Hello from Claude"}]
    }
    mock_post.return_value = mock_response

    client = SimpleAnthropicClient(api_key="anthropic-key", model="claude-haiku-4-5")
    res = client.create_message("Hello Anthropic", max_tokens=100, timeout=30.0)

    assert res == "Hello from Claude"
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.anthropic.com/v1/messages"
    assert kwargs["headers"]["x-api-key"] == "anthropic-key"
    assert kwargs["headers"]["anthropic-version"] == "2023-06-01"
    assert kwargs["json"]["model"] == "claude-haiku-4-5"
    assert kwargs["json"]["max_tokens"] == 100
    assert kwargs["json"]["messages"] == [{"role": "user", "content": "Hello Anthropic"}]
    assert kwargs["timeout"] == 30.0

def test_gemini_client(mocker):
    mock_post = mocker.patch("httpx.post")
    
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{"text": "Hello from Gemini"}]
            }
        }]
    }
    mock_post.return_value = mock_response

    client = GeminiClient(api_key="gemini-key", model="gemini-1.5-flash")
    res = client.generate_content("Hello Gemini", timeout=15.0)

    assert res == "Hello from Gemini"
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    assert kwargs["params"] == {"key": "gemini-key"}
    assert kwargs["json"]["contents"] == [{"parts": [{"text": "Hello Gemini"}]}]
    assert kwargs["timeout"] == 15.0

def test_data_request_openai(mocker):
    mock_client = mocker.Mock()
    mocker.patch("openai.OpenAI", return_value=mock_client)
    
    mock_completion = mocker.Mock()
    mock_completion.choices = [
        mocker.Mock(message=mocker.Mock(content="Hello OpenAI"))
    ]
    mock_client.chat.completions.create.return_value = mock_completion

    ConfigManager.save_settings({
        "selectedApi": "openai",
        "openaiModel": "gpt-4o-mini",
        "netTimeout": 20.0,
        "emulate": "no",
        "encryptionKey": "test-salt"
    })
    ConfigManager.save_credentials({"apiKey": "openai-key"}, key="test-salt")

    res = data_request.send_prompt_to_llm("test prompt")
    assert res == "Hello OpenAI"
    
    mock_client.chat.completions.create.assert_called_once()
    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["model"] == "gpt-4o-mini"
    assert kwargs["messages"] == [{"role": "user", "content": "test prompt"}]

def test_data_request_openrouter(mocker):
    mock_client = mocker.Mock()
    mocker.patch("openai.OpenAI", return_value=mock_client)
    
    mock_completion = mocker.Mock()
    mock_completion.choices = [
        mocker.Mock(message=mocker.Mock(content="Hello OpenRouter"))
    ]
    mock_client.chat.completions.create.return_value = mock_completion

    ConfigManager.save_settings({
        "selectedApi": "openrouter",
        "openrouterModel": "google/gemini-2.0-flash-lite-001",
        "netTimeout": 10.0,
        "emulate": "no",
        "encryptionKey": "test-salt"
    })
    ConfigManager.save_credentials({"openrouterKey": "openrouter-key"}, key="test-salt")

    res = data_request.send_prompt_to_llm("test prompt")
    assert res == "Hello OpenRouter"
    
    mock_client.chat.completions.create.assert_called_once()
    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["model"] == "google/gemini-2.0-flash-lite-001"
    assert kwargs["messages"] == [{"role": "user", "content": "test prompt"}]
    assert kwargs["extra_headers"] == {
        "HTTP-Referer": "https://ankiweb.net/",
        "X-Title": "IntelliFiller Anki Addon",
    }

def test_data_request_anthropic(mocker):
    mock_post = mocker.patch("httpx.post")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "content": [{"text": "Hello Anthropic"}]
    }
    mock_post.return_value = mock_response

    ConfigManager.save_settings({
        "selectedApi": "anthropic",
        "anthropicModel": "claude-3-haiku",
        "netTimeout": 18.0,
        "emulate": "no",
        "encryptionKey": "test-salt"
    })
    ConfigManager.save_credentials({"anthropicKey": "anthropic-key"}, key="test-salt")

    res = data_request.send_prompt_to_llm("test prompt")
    assert res == "Hello Anthropic"

    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.anthropic.com/v1/messages"
    assert kwargs["json"]["model"] == "claude-3-haiku"
    assert kwargs["json"]["messages"] == [{"role": "user", "content": "test prompt"}]
    assert kwargs["timeout"] == 18.0


def test_data_request_gemini(mocker):
    mock_post = mocker.patch("httpx.post")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Hello Gemini"}]}}]
    }
    mock_post.return_value = mock_response

    ConfigManager.save_settings({
        "selectedApi": "gemini",
        "geminiModel": "gemini-1.5-flash",
        "netTimeout": 16.0,
        "emulate": "no",
        "encryptionKey": "test-salt"
    })
    ConfigManager.save_credentials({"geminiKey": "gemini-key"}, key="test-salt")

    res = data_request.send_prompt_to_llm("test prompt")
    assert res == "Hello Gemini"

    args, kwargs = mock_post.call_args
    assert args[0] == "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    assert kwargs["params"] == {"key": "gemini-key"}
    assert kwargs["json"]["contents"] == [{"parts": [{"text": "test prompt"}]}]
    assert kwargs["timeout"] == 16.0


def test_data_request_emulate(mocker):
    ConfigManager.save_settings({"selectedApi": "openai", "emulate": "yes"})

    res = data_request.send_prompt_to_llm("emulated prompt")
    assert "fake response" in res.lower()
    assert "emulated prompt" in res


def test_data_request_openrouter_uses_api_key(mocker):
    mock_client = mocker.Mock()
    mocker.patch("openai.OpenAI", return_value=mock_client)
    mock_client.chat.completions.create.return_value = mocker.Mock(
        choices=[mocker.Mock(message=mocker.Mock(content="ok"))]
    )

    ConfigManager.save_settings({
        "selectedApi": "openrouter",
        "openrouterModel": "google/gemini-2.0-flash-lite-001",
        "netTimeout": 10.0,
        "emulate": "no",
        "encryptionKey": "test-salt",
    })
    ConfigManager.save_credentials({"openrouterKey": "openrouter-key"}, key="test-salt")

    data_request.send_prompt_to_llm("hi")
    args, kwargs = openai.OpenAI.call_args
    assert kwargs["api_key"] == "openrouter-key"
    assert kwargs["base_url"] == "https://openrouter.ai/api/v1"


def test_data_request_propagates_openai_error(mocker):
    mock_client = mocker.Mock()
    mocker.patch("openai.OpenAI", return_value=mock_client)
    mock_client.chat.completions.create.side_effect = RuntimeError("502 Bad Gateway")

    ConfigManager.save_settings({
        "selectedApi": "openai",
        "openaiModel": "gpt-4o-mini",
        "netTimeout": 5.0,
        "emulate": "no",
        "encryptionKey": "test-salt",
    })
    ConfigManager.save_credentials({"apiKey": "k"}, key="test-salt")

    with pytest.raises(RuntimeError, match="502"):
        data_request.send_prompt_to_llm("hi")


def test_data_request_propagates_anthropic_error(mocker):
    mocker.patch("httpx.post", side_effect=httpx.ConnectError("connection refused"))
    ConfigManager.save_settings({
        "selectedApi": "anthropic",
        "netTimeout": 5.0,
        "emulate": "no",
        "encryptionKey": "test-salt",
    })
    ConfigManager.save_credentials({"anthropicKey": "k"}, key="test-salt")

    with pytest.raises(Exception, match="Anthropic"):
        data_request.send_prompt_to_llm("hi")


def test_data_request_propagates_gemini_error(mocker):
    mocker.patch("httpx.post", side_effect=httpx.TimeoutException("read timeout"))
    ConfigManager.save_settings({
        "selectedApi": "gemini",
        "netTimeout": 5.0,
        "emulate": "no",
        "encryptionKey": "test-salt",
    })
    ConfigManager.save_credentials({"geminiKey": "k"}, key="test-salt")

    with pytest.raises(Exception, match="Gemini"):
        data_request.send_prompt_to_llm("hi")


def test_anthropic_client_wraps_unexpected_payload(mocker):
    mock_post = mocker.patch("httpx.post")
    mock_post.return_value = mocker.Mock(json=lambda: {"unexpected": "shape"})

    client = SimpleAnthropicClient(api_key="k", model="m")
    with pytest.raises(Exception, match="Anthropic"):
        client.create_message("hi")


def test_gemini_client_wraps_unexpected_payload(mocker):
    mock_post = mocker.patch("httpx.post")
    mock_post.return_value = mocker.Mock(json=lambda: {"unexpected": "shape"})

    client = GeminiClient(api_key="k", model="m")
    with pytest.raises(Exception, match="Gemini"):
        client.generate_content("hi")
