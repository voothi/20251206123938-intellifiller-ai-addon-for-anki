import pytest
import json
import io
from urllib.error import HTTPError
from IntelliFiller.config_manager import ConfigManager
from IntelliFiller import data_request
from IntelliFiller.ollama_client import OllamaClient


def test_ollama_client_native(mocker):
    mock_urlopen = mocker.patch("urllib.request.urlopen")

    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({"response": "Local native response"}).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    client = OllamaClient(
        api_url="http://localhost:11434/api/generate",
        model="llama3-test"
    )
    res = client.generate_content("Translate: Hello")

    assert res == "Local native response"
    mock_urlopen.assert_called_once()
    args, kwargs = mock_urlopen.call_args
    req = args[0]
    assert req.full_url == "http://localhost:11434/api/generate"
    
    data = json.loads(req.data.decode("utf-8"))
    assert data["model"] == "llama3-test"
    assert data["prompt"] == "Translate: Hello"
    assert data["stream"] is False
    
    req_headers = {k.lower(): v for k, v in req.header_items()}
    assert "authorization" not in req_headers


def test_ollama_client_chat_completions(mocker):
    mock_urlopen = mocker.patch("urllib.request.urlopen")

    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({
        "choices": [
            {
                "message": {
                    "content": "Chat completions response"
                }
            }
        ]
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    client = OllamaClient(
        api_url="http://localhost:11434/v1/chat/completions",
        model="llama3-test"
    )
    res = client.generate_content("Translate: Hello")

    assert res == "Chat completions response"
    mock_urlopen.assert_called_once()
    args, kwargs = mock_urlopen.call_args
    req = args[0]
    assert req.full_url == "http://localhost:11434/v1/chat/completions"
    
    data = json.loads(req.data.decode("utf-8"))
    assert data["model"] == "llama3-test"
    assert data["messages"][0]["content"] == "Translate: Hello"
    
    req_headers = {k.lower(): v for k, v in req.header_items()}
    assert "authorization" not in req_headers


def test_send_prompt_to_llm_ollama_local(mocker):
    ConfigManager.save_settings({
        "selectedApi": "ollama",
        "ollamaUrl": "http://localhost:11434/api/generate",
        "ollamaModel": "llama3-test",
        "emulate": "no"
    })

    client_instance = mocker.Mock()
    client_instance.generate_content.return_value = "Mocked local response"
    mocker.patch("IntelliFiller.data_request.OllamaClient", return_value=client_instance)

    res = data_request.send_prompt_to_llm("Hello local")
    assert res == "Mocked local response"

    client_instance.generate_content.assert_called_once()
    args, kwargs = client_instance.generate_content.call_args
    assert args[0] == "Hello local"
    assert kwargs["timeout"] == 10.0


def test_send_prompt_to_llm_ollama_cloud(mocker):
    ConfigManager.save_settings({
        "selectedApi": "ollama_cloud",
        "ollamaCloudUrl": "https://ollama.com/v1",
        "ollamaCloudModel": "llama3-cloud-test",
        "emulate": "no",
        "encryptionKey": "test-cloud-salt"
    })

    ConfigManager.save_credentials({
        "ollamaCloudKey": "secret-cloud-key"
    }, key="test-cloud-salt", obfuscate=True)

    client_instance = mocker.Mock()
    client_instance.generate_content.return_value = "Mocked cloud response"
    mock_cls = mocker.patch("IntelliFiller.data_request.OllamaClient", return_value=client_instance)

    res = data_request.send_prompt_to_llm("Hello cloud")
    assert res == "Mocked cloud response"

    mock_cls.assert_called_once()
    kwargs = mock_cls.call_args.kwargs
    assert kwargs["api_url"] == "https://ollama.com/v1"
    assert kwargs["api_key"] == "secret-cloud-key"
    assert kwargs["model"] == "llama3-cloud-test"
    client_instance.generate_content.assert_called_once()
    assert client_instance.generate_content.call_args.args[0] == "Hello cloud"


def test_ollama_client_cloud_domain_override(mocker):
    mock_urlopen = mocker.patch("urllib.request.urlopen")

    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({
        "choices": [
            {
                "message": {
                    "content": "Normalized response"
                }
            }
        ]
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    client = OllamaClient(
        api_url="https://ollama.com/api/generate",
        api_key="my-key",
        model="cloud-model"
    )
    res = client.generate_content("Hello")
    assert res == "Normalized response"

    mock_urlopen.assert_called_once()
    args, kwargs = mock_urlopen.call_args
    req = args[0]
    assert req.full_url == "https://ollama.com/v1/chat/completions"
    
    data = json.loads(req.data.decode("utf-8"))
    assert data["messages"][0]["content"] == "Hello"


def test_ollama_client_default_url_no_path():
    client = OllamaClient(api_url="http://localhost:11434", model="llama3")
    assert client.api_url.endswith("/api/generate")


def test_ollama_client_v1_base_normalized():
    client = OllamaClient(api_url="http://localhost:11434/v1", model="llama3")
    assert client.api_url.endswith("/v1/chat/completions")


def test_ollama_client_unexpected_response_raises(mocker):
    mock_urlopen = mocker.patch("urllib.request.urlopen")

    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({"unexpected": "shape"}).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    client = OllamaClient(api_url="http://localhost:11434/api/generate", model="llama3")
    with pytest.raises(Exception, match="Ollama"):
        client.generate_content("Hello")


@pytest.mark.parametrize("input_url,expected_suffix", [
    ("http://localhost:11434", "/api/generate"),
    ("http://localhost:11434/v1", "/v1/chat/completions"),
    ("http://localhost:11434/v1/", "/v1/chat/completions"),
    ("http://localhost:11434/v1/chat/completions", "/v1/chat/completions"),
    ("http://localhost:11434/v1/completions", "/v1/completions"),
    ("http://localhost:11434/api/generate", "/generate"),
    ("http://localhost:11434/other", "/other/generate"),
    ("https://ollama.com/api/generate", "/v1/chat/completions"),
])
def test_ollama_client_url_normalization(input_url, expected_suffix):
    client = OllamaClient(api_url=input_url, model="llama3")
    assert client.api_url.endswith(expected_suffix)


def test_ollama_client_trailing_slash_on_bare_host():
    client = OllamaClient(api_url="http://localhost:11434/", model="llama3")
    assert client.api_url.endswith("/generate")
    assert "//generate" not in client.api_url.replace("http://", "")


def test_ollama_client_v1_chat_without_completions_appended():
    client = OllamaClient(api_url="http://localhost:11434/v1/chat", model="llama3")
    assert client.api_url.endswith("/chat/completions")


def test_ollama_client_empty_url_falls_back_to_default():
    client = OllamaClient(api_url="", model="llama3")
    assert client.api_url == "http://localhost:11434/api/generate"


def test_ollama_client_http_error_raises(mocker):
    fp = io.BytesIO(b"Connection error details")
    err = HTTPError("http://localhost:11434/api/generate", 500, "Internal Server Error", {}, fp)
    mocker.patch("urllib.request.urlopen", side_effect=err)

    client = OllamaClient(api_url="http://localhost:11434/api/generate", model="llama3")
    with pytest.raises(Exception, match="Ollama"):
        client.generate_content("hi")


def test_send_prompt_to_llm_ollama_cloud_without_key(mocker):
    ConfigManager.save_settings({
        "selectedApi": "ollama_cloud",
        "ollamaCloudUrl": "https://ollama.com/v1",
        "ollamaCloudModel": "llama3-cloud-test",
        "emulate": "no",
    })

    client_instance = mocker.Mock()
    client_instance.generate_content.return_value = "no key response"
    mock_cls = mocker.patch("IntelliFiller.data_request.OllamaClient", return_value=client_instance)

    res = data_request.send_prompt_to_llm("hi")
    assert res == "no key response"

    mock_cls.assert_called_once()
    kwargs = mock_cls.call_args.kwargs
    # No key stored -> OllamaClient receives "" for api_key
    assert kwargs["api_key"] == ""
