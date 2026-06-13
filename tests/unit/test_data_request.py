import pytest
from unittest.mock import patch, MagicMock
import urllib.error
from IntelliFiller.data_request import (
    get_platform_specific_vendor,
    _http_chat_completion,
    _provider_defaults,
    test_connection as check_connection,
    send_prompt_to_llm
)


def test_get_platform_specific_vendor_mac_arm():
    with patch('platform.system', return_value='darwin'), \
         patch('platform.machine', return_value='arm64'):
        assert get_platform_specific_vendor() == 'darwin_arm64'

def test_get_platform_specific_vendor_mac_x86():
    with patch('platform.system', return_value='darwin'), \
         patch('platform.machine', return_value='x86_64'):
        assert get_platform_specific_vendor() == 'darwin_x86_64'

def test_get_platform_specific_vendor_linux():
    with patch('platform.system', return_value='linux'), \
         patch('platform.machine', return_value='x86_64'):
        assert get_platform_specific_vendor() == 'linux'

def test_get_platform_specific_vendor_unsupported():
    with patch('platform.system', return_value='sunos'), \
         patch('platform.machine', return_value='sparc'):
        with pytest.raises(RuntimeError, match="Unsupported platform: sunos sparc"):
            get_platform_specific_vendor()

@patch('urllib.request.urlopen')
def test_http_chat_completion_http_error(mock_urlopen):
    # Simulate an HTTPError
    mock_error = urllib.error.HTTPError(
        url="http://fake", code=400, msg="Bad Request", hdrs={}, fp=None
    )
    # Give it a read method that returns some error body
    mock_error.read = MagicMock(return_value=b'{"error": "bad request"}')
    mock_urlopen.side_effect = mock_error

    with pytest.raises(Exception, match=r"HTTP 400 Bad Request - \{\"error\": \"bad request\"\}"):
        _http_chat_completion("http://fake", "key", "model", "prompt")

@patch('urllib.request.urlopen')
def test_http_chat_completion_url_error(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.URLError("connection refused")
    with pytest.raises(Exception, match=r"Network error: <urlopen error connection refused>"):
        _http_chat_completion("http://fake", "key", "model", "prompt")

@patch('urllib.request.urlopen')
def test_http_chat_completion_key_error(mock_urlopen):
    # Missing 'choices' in response
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"bad_key": "val"}'
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    with pytest.raises(Exception, match=r"Unexpected response structure \(missing key: 'choices'\)"):
        _http_chat_completion("http://fake", "key", "model", "prompt")

@patch('urllib.request.urlopen')
def test_http_chat_completion_general_error(mock_urlopen):
    mock_urlopen.side_effect = ValueError("Some weird error")
    with pytest.raises(Exception, match=r"Request failed: Some weird error"):
        _http_chat_completion("http://fake", "key", "model", "prompt")

def test_provider_defaults():
    # OpenAI
    url, key, model, hdrs = _provider_defaults({'selectedApi': 'openai', 'apiKey': 'test-key'})
    assert url == "https://api.openai.com/v1/chat/completions"
    assert key == "test-key"
    assert model == "gpt-4o-mini"
    assert hdrs is None

    # OpenRouter
    url, key, model, hdrs = _provider_defaults({'selectedApi': 'openrouter', 'openrouterKey': 'or-key', 'openrouterModel': 'or-model'})
    assert url == "https://openrouter.ai/api/v1/chat/completions"
    assert key == "or-key"
    assert model == "or-model"
    assert hdrs is not None
    assert "HTTP-Referer" in hdrs

    # Custom
    url, key, model, hdrs = _provider_defaults({'selectedApi': 'custom', 'customUrl': 'http://c', 'customKey': 'ck'})
    assert url == "http://c"
    assert key == "ck"
    assert model == "my-model"
    assert hdrs is None

    # Ollama / Anthropic / Gemini return None, None, None, None
    assert _provider_defaults({'selectedApi': 'ollama'}) == (None, None, None, None)
    assert _provider_defaults({'selectedApi': 'anthropic'}) == (None, None, None, None)
    assert _provider_defaults({'selectedApi': 'gemini'}) == (None, None, None, None)

    # Fallback
    url, key, model, hdrs = _provider_defaults({'selectedApi': 'unknown', 'apiKey': 'test-key'})
    assert url == "https://api.openai.com/v1/chat/completions"

@patch('IntelliFiller.data_request._http_chat_completion')
def test_test_connection_openai(mock_http):
    mock_http.return_value = "OK"
    config = {'selectedApi': 'openai', 'apiKey': 'key'}
    ok, msg = check_connection(config)
    assert ok is True
    assert "openai connection OK" in msg

@patch('IntelliFiller.data_request.SimpleAnthropicClient')
def test_test_connection_anthropic(mock_anthropic):
    mock_instance = MagicMock()
    mock_instance.create_message.return_value = "OK"
    mock_anthropic.return_value = mock_instance
    config = {'selectedApi': 'anthropic', 'anthropicKey': 'key'}
    ok, msg = check_connection(config)
    assert ok is True
    assert "Anthropic connection OK" in msg

@patch('IntelliFiller.data_request.GeminiClient')
def test_test_connection_gemini(mock_gemini):
    mock_instance = MagicMock()
    mock_instance.generate_content.return_value = "OK"
    mock_gemini.return_value = mock_instance
    config = {'selectedApi': 'gemini', 'geminiKey': 'key'}
    ok, msg = check_connection(config)
    assert ok is True
    assert "Gemini connection OK" in msg

@patch('IntelliFiller.data_request.OllamaClient')
def test_test_connection_ollama(mock_ollama):
    mock_instance = MagicMock()
    mock_instance.generate_content.return_value = "OK"
    mock_ollama.return_value = mock_instance
    config = {'selectedApi': 'ollama'}
    ok, msg = check_connection(config)
    assert ok is True
    assert "Ollama connection OK" in msg

@patch('IntelliFiller.data_request.OllamaClient')
def test_test_connection_ollama_cloud(mock_ollama):
    mock_instance = MagicMock()
    mock_instance.generate_content.return_value = "OK"
    mock_ollama.return_value = mock_instance
    config = {'selectedApi': 'ollama_cloud'}
    ok, msg = check_connection(config)
    assert ok is True
    assert "Ollama Cloud connection OK" in msg

def test_test_connection_missing_keys():
    ok, msg = check_connection({'selectedApi': 'openai'}) # missing api key
    assert ok is False
    assert "OpenAI API key is missing" in msg

    ok, msg = check_connection({'selectedApi': 'openrouter'}) # missing api key
    assert ok is False
    assert "OpenRouter API key is missing" in msg

    ok, msg = check_connection({'selectedApi': 'custom', 'customUrl': ''}) # missing custom url
    assert ok is False
    assert "Custom base URL is missing" in msg

@patch('IntelliFiller.data_request.ConfigManager')
@patch('IntelliFiller.data_request._http_chat_completion')
def test_send_prompt_custom(mock_http, mock_cm):
    mock_cm.load_settings.return_value = {'selectedApi': 'custom', 'customUrl': 'http://c'}
    mock_cm.load_credentials.return_value = {'customKey': 'k'}
    mock_http.return_value = "custom response"
    
    resp = send_prompt_to_llm("hello")
    assert resp == "custom response"
    mock_http.assert_called_once()
