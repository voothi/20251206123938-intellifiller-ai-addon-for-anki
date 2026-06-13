import pytest
import json
import io
from urllib.error import HTTPError
from IntelliFiller.anthropic_client import SimpleAnthropicClient
from IntelliFiller.gemini_client import GeminiClient
from IntelliFiller.config_manager import ConfigManager
from IntelliFiller import data_request


def test_anthropic_client(mocker):
    mock_urlopen = mocker.patch("urllib.request.urlopen")

    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({
        "content": [{"text": "Hello from Claude"}]
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    client = SimpleAnthropicClient(api_key="anthropic-key", model="claude-haiku-4-5")
    res = client.create_message("Hello Anthropic", max_tokens=100, timeout=30.0)

    assert res == "Hello from Claude"
    mock_urlopen.assert_called_once()
    args, kwargs = mock_urlopen.call_args
    req = args[0]
    assert req.full_url == "https://api.anthropic.com/v1/messages"
    
    req_headers = {k.lower(): v for k, v in req.header_items()}
    assert req_headers["x-api-key"] == "anthropic-key"
    assert req_headers["anthropic-version"] == "2023-06-01"
    assert req_headers["content-type"] == "application/json"
    
    data = json.loads(req.data.decode("utf-8"))
    assert data["model"] == "claude-haiku-4-5"
    assert data["max_tokens"] == 100
    assert data["messages"] == [{"role": "user", "content": "Hello Anthropic"}]
    assert kwargs["timeout"] == 30.0


def test_gemini_client(mocker):
    mock_urlopen = mocker.patch("urllib.request.urlopen")

    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({
        "candidates": [{
            "content": {
                "parts": [{"text": "Hello from Gemini"}]
            }
        }]
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    client = GeminiClient(api_key="gemini-key", model="gemini-1.5-flash")
    res = client.generate_content("Hello Gemini", timeout=15.0)

    assert res == "Hello from Gemini"
    mock_urlopen.assert_called_once()
    args, kwargs = mock_urlopen.call_args
    req = args[0]
    assert req.full_url == "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=gemini-key"
    
    req_headers = {k.lower(): v for k, v in req.header_items()}
    assert req_headers["content-type"] == "application/json"
    
    data = json.loads(req.data.decode("utf-8"))
    assert data["contents"] == [{"parts": [{"text": "Hello Gemini"}]}]
    assert kwargs["timeout"] == 15.0


def test_data_request_openai(mocker):
    mock_urlopen = mocker.patch("urllib.request.urlopen")

    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({
        "choices": [{"message": {"content": "Hello OpenAI"}}]
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

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

    mock_urlopen.assert_called_once()
    args, kwargs = mock_urlopen.call_args
    req = args[0]
    assert req.full_url == "https://api.openai.com/v1/chat/completions"
    
    req_headers = {k.lower(): v for k, v in req.header_items()}
    assert req_headers["authorization"] == "Bearer openai-key"
    assert req_headers["content-type"] == "application/json"
    
    data = json.loads(req.data.decode("utf-8"))
    assert data["model"] == "gpt-4o-mini"
    assert data["messages"] == [{"role": "user", "content": "test prompt"}]
    assert kwargs["timeout"] == 20.0


def test_data_request_openrouter(mocker):
    mock_urlopen = mocker.patch("urllib.request.urlopen")

    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({
        "choices": [{"message": {"content": "Hello OpenRouter"}}]
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

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

    mock_urlopen.assert_called_once()
    args, kwargs = mock_urlopen.call_args
    req = args[0]
    assert req.full_url == "https://openrouter.ai/api/v1/chat/completions"
    
    req_headers = {k.lower(): v for k, v in req.header_items()}
    assert req_headers["authorization"] == "Bearer openrouter-key"
    assert req_headers["http-referer"] == "https://ankiweb.net/"
    assert req_headers["x-title"] == "IntelliFiller Anki Addon"
    
    data = json.loads(req.data.decode("utf-8"))
    assert data["model"] == "google/gemini-2.0-flash-lite-001"
    assert data["messages"] == [{"role": "user", "content": "test prompt"}]
    assert kwargs["timeout"] == 10.0


def test_data_request_anthropic(mocker):
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
    mock_urlopen = mocker.patch("urllib.request.urlopen")

    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({
        "choices": [{"message": {"content": "ok"}}]
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    ConfigManager.save_settings({
        "selectedApi": "openrouter",
        "openrouterModel": "google/gemini-2.0-flash-lite-001",
        "netTimeout": 10.0,
        "emulate": "no",
        "encryptionKey": "test-salt",
    })
    ConfigManager.save_credentials({"openrouterKey": "openrouter-key"}, key="test-salt")

    data_request.send_prompt_to_llm("hi")
    
    mock_urlopen.assert_called_once()
    args, kwargs = mock_urlopen.call_args
    req = args[0]
    assert req.full_url == "https://openrouter.ai/api/v1/chat/completions"
    
    req_headers = {k.lower(): v for k, v in req.header_items()}
    assert req_headers["authorization"] == "Bearer openrouter-key"


def test_data_request_propagates_openai_error(mocker):
    fp = io.BytesIO(b'{"error":{"message":"Invalid key"}}')
    err = HTTPError("https://api.openai.com/v1/chat/completions", 401, "Unauthorized", {}, fp)
    mocker.patch("urllib.request.urlopen", side_effect=err)

    ConfigManager.save_settings({
        "selectedApi": "openai",
        "openaiModel": "gpt-4o-mini",
        "netTimeout": 5.0,
        "emulate": "no",
        "encryptionKey": "test-salt",
    })
    ConfigManager.save_credentials({"apiKey": "k"}, key="test-salt")

    with pytest.raises(Exception, match="HTTP 401"):
        data_request.send_prompt_to_llm("hi")


def test_data_request_propagates_anthropic_error(mocker):
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
    mock_urlopen = mocker.patch("urllib.request.urlopen")

    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({"unexpected": "shape"}).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    client = SimpleAnthropicClient(api_key="k", model="m")
    with pytest.raises(Exception, match="Anthropic"):
        client.create_message("hi")


def test_gemini_client_wraps_unexpected_payload(mocker):
    mock_urlopen = mocker.patch("urllib.request.urlopen")

    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({"unexpected": "shape"}).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    client = GeminiClient(api_key="k", model="m")
    with pytest.raises(Exception, match="Gemini"):
        client.generate_content("hi")
