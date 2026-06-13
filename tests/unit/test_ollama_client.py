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


