import pytest
import httpx
import openai
from IntelliFiller.anthropic_client import SimpleAnthropicClient
from IntelliFiller.gemini_client import GeminiClient
from IntelliFiller.config_manager import ConfigManager
from IntelliFiller import data_request


def test_anthropic_client(mocker):
    # NOTE: This test verifies SimpleAnthropicClient's internal HTTP request shape.
    # When migrated to urllib per the 20260613114219-port-fork-improvements spec,
    # update this mock target to urllib.request.urlopen. The data_request-level
    # tests in this file mock at the client class boundary and are
    # transport-agnostic.
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
    # See migration note in test_anthropic_client.
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
    # Transport-agnostic: mock openai.OpenAI directly.
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
    # Transport-agnostic: mock openai.OpenAI directly.
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
    # Transport-agnostic: mock SimpleAnthropicClient at the data_request boundary.
    client_instance = mocker.Mock()
    client_instance.create_message.return_value = "Hello Anthropic"
    mock_cls = mocker.patch(
        "IntelliFiller.data_request.SimpleAnthropicClient", return_value=client_instance
    )

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

    mock_cls.assert_called_once()
    kwargs = mock_cls.call_args.kwargs
    assert kwargs["api_key"] == "anthropic-key"
    assert kwargs["model"] == "claude-3-haiku"
    client_instance.create_message.assert_called_once()
    assert client_instance.create_message.call_args.args[0] == "test prompt"
    assert client_instance.create_message.call_args.kwargs["timeout"] == 18.0


def test_data_request_gemini(mocker):
    # Transport-agnostic: mock GeminiClient at the data_request boundary.
    client_instance = mocker.Mock()
    client_instance.generate_content.return_value = "Hello Gemini"
    mock_cls = mocker.patch(
        "IntelliFiller.data_request.GeminiClient", return_value=client_instance
    )

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

    mock_cls.assert_called_once()
    kwargs = mock_cls.call_args.kwargs
    assert kwargs["api_key"] == "gemini-key"
    assert kwargs["model"] == "gemini-1.5-flash"
    client_instance.generate_content.assert_called_once()
    assert client_instance.generate_content.call_args.args[0] == "test prompt"
    assert client_instance.generate_content.call_args.kwargs["timeout"] == 16.0


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
    # Mock the client class; raising from the client exercises the data_request
    # try/except re-raise path.
    client_instance = mocker.Mock()
    client_instance.create_message.side_effect = Exception("Error calling Anthropic API: connection refused")
    mocker.patch("IntelliFiller.data_request.SimpleAnthropicClient", return_value=client_instance)

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
    client_instance = mocker.Mock()
    client_instance.generate_content.side_effect = Exception("Error calling Gemini API: read timeout")
    mocker.patch("IntelliFiller.data_request.GeminiClient", return_value=client_instance)

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
    # See migration note in test_anthropic_client.
    mock_post = mocker.patch("httpx.post")
    mock_post.return_value = mocker.Mock(json=lambda: {"unexpected": "shape"})

    client = SimpleAnthropicClient(api_key="k", model="m")
    with pytest.raises(Exception, match="Anthropic"):
        client.create_message("hi")


def test_gemini_client_wraps_unexpected_payload(mocker):
    # See migration note in test_anthropic_client.
    mock_post = mocker.patch("httpx.post")
    mock_post.return_value = mocker.Mock(json=lambda: {"unexpected": "shape"})

    client = GeminiClient(api_key="k", model="m")
    with pytest.raises(Exception, match="Gemini"):
        client.generate_content("hi")
