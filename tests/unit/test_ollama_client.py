import pytest
import httpx
from IntelliFiller.config_manager import ConfigManager
from IntelliFiller import data_request
from IntelliFiller.ollama_client import OllamaClient

def test_ollama_client_native(mocker):
    # Mock httpx.post
    mock_post = mocker.patch("httpx.post")
    
    # Configure mock response
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
    # Mock httpx.post
    mock_post = mocker.patch("httpx.post")
    
    # Configure mock response for OpenAI-compatible chat API
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
    # Set settings first (uses local Ollama)
    ConfigManager.save_settings({
        "selectedApi": "ollama",
        "ollamaUrl": "http://localhost:11434/api/generate",
        "ollamaModel": "llama3-test",
        "emulate": "no"
    })
    
    # Mock httpx.post
    mock_post = mocker.patch("httpx.post")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"response": "Mocked local response"}
    mock_post.return_value = mock_response

    res = data_request.send_prompt_to_llm("Hello local")
    assert res == "Mocked local response"
    
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["model"] == "llama3-test"
    assert kwargs["json"]["prompt"] == "Hello local"

def test_send_prompt_to_llm_ollama_cloud(mocker):
    # Set settings first (uses Ollama Cloud)
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
    
    # Mock httpx.post
    mock_post = mocker.patch("httpx.post")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Mocked cloud response"
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    res = data_request.send_prompt_to_llm("Hello cloud")
    assert res == "Mocked cloud response"
    
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://ollama.com/v1/chat/completions"
    assert kwargs["json"]["model"] == "llama3-cloud-test"
    assert kwargs["json"]["messages"][0]["content"] == "Hello cloud"
    assert kwargs["headers"]["Authorization"] == "Bearer secret-cloud-key"

def test_ollama_client_cloud_domain_override(mocker):
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
    mock_post = mocker.patch("httpx.post")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"unexpected": "shape"}
    mock_post.return_value = mock_response

    client = OllamaClient(api_url="http://localhost:11434/api/generate", model="llama3")
    with pytest.raises(Exception):
        client.generate_content("Hello")

