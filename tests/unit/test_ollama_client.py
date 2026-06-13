import pytest
import httpx
from IntelliFiller.config_manager import ConfigManager
from IntelliFiller import data_request
from IntelliFiller.ollama_client import OllamaClient


def test_ollama_client_native(mocker):
    # NOTE: This test verifies the client-internal HTTP request shape (URL, payload, headers).
    # It mocks httpx.post directly. When the client is migrated to urllib (per the
    # 20260613114219-port-fork-improvements spec), update this mock target to
    # urllib.request.urlopen. The data_request-level tests in this file are
    # transport-agnostic and do not need to change.
    mock_post = mocker.patch("httpx.post")

    mock_response = mocker.Mock()
    mock_response.json.return_value = {"response": "Local native response"}
    mock_post.return_value = mock_response

    client = OllamaClient(
        api_url="http://localhost:11434/api/generate",
        model="llama3-test"
    )
    res = client.generate_content("Translate: Hello")

    assert res == "Local native response"
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "http://localhost:11434/api/generate"
    assert kwargs["json"]["model"] == "llama3-test"
    assert kwargs["json"]["prompt"] == "Translate: Hello"
    assert kwargs["json"]["stream"] is False
    assert "Authorization" not in kwargs["headers"]


def test_ollama_client_chat_completions(mocker):
    # See migration note in test_ollama_client_native.
    mock_post = mocker.patch("httpx.post")

    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Chat completions response"
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    client = OllamaClient(
        api_url="http://localhost:11434/v1/chat/completions",
        model="llama3-test"
    )
    res = client.generate_content("Translate: Hello")

    assert res == "Chat completions response"
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "http://localhost:11434/v1/chat/completions"
    assert kwargs["json"]["model"] == "llama3-test"
    assert kwargs["json"]["messages"][0]["content"] == "Translate: Hello"
    assert "Authorization" not in kwargs["headers"]


def test_send_prompt_to_llm_ollama_local(mocker):
    # Mock the OllamaClient class so this test is transport-agnostic. It will
    # keep working whether the client uses httpx, urllib, or anything else.
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
    # Transport-agnostic: mock the OllamaClient class, not httpx.
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
    # See migration note in test_ollama_client_native.
    mock_post = mocker.patch("httpx.post")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Normalized response"
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    client = OllamaClient(
        api_url="https://ollama.com/api/generate",
        api_key="my-key",
        model="cloud-model"
    )
    res = client.generate_content("Hello")
    assert res == "Normalized response"

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://ollama.com/v1/chat/completions"
    assert kwargs["json"]["messages"][0]["content"] == "Hello"


def test_ollama_client_default_url_no_path():
    client = OllamaClient(api_url="http://localhost:11434", model="llama3")
    assert client.api_url.endswith("/api/generate")


def test_ollama_client_v1_base_normalized():
    client = OllamaClient(api_url="http://localhost:11434/v1", model="llama3")
    assert client.api_url.endswith("/v1/chat/completions")


def test_ollama_client_unexpected_response_raises(mocker):
    # See migration note in test_ollama_client_native.
    mock_post = mocker.patch("httpx.post")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"unexpected": "shape"}
    mock_post.return_value = mock_response

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
    # See migration note in test_ollama_client_native.
    mocker.patch("httpx.post", side_effect=httpx.ConnectError("conn refused"))
    client = OllamaClient(api_url="http://localhost:11434/api/generate", model="llama3")
    with pytest.raises(Exception, match="Ollama"):
        client.generate_content("hi")


def test_send_prompt_to_llm_ollama_cloud_without_key(mocker):
    # Transport-agnostic: mock the OllamaClient class.
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
    # No key stored -> OllamaClient receives None for api_key
    assert kwargs["api_key"] is None
