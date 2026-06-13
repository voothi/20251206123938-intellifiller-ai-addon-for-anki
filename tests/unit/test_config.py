import os
from IntelliFiller.config_manager import ConfigManager

def test_default_config():
    config = ConfigManager.get_full_config()
    assert isinstance(config, dict)
    assert config.get("prompts") == []

def test_save_and_load_settings():
    settings = {"selectedApi": "ollama", "netTimeout": 15}
    ConfigManager.save_settings(settings)
    
    loaded = ConfigManager.load_settings()
    assert loaded.get("selectedApi") == "ollama"
    assert loaded.get("netTimeout") == 15

def test_save_and_load_credentials():
    credentials = {"ollamaUrl": "http://localhost:11434/api/generate", "ollamaModel": "llama3-test"}
    ConfigManager.save_credentials(credentials, key="test-key", obfuscate=True)
    
    loaded = ConfigManager.load_credentials(key="test-key")
    assert loaded.get("ollamaUrl") == "http://localhost:11434/api/generate"
    assert loaded.get("ollamaModel") == "llama3-test"

def test_get_full_config():
    settings = {"selectedApi": "ollama", "netTimeout": 12, "encryptionKey": "my-secret-salt"}
    credentials = {"ollamaUrl": "http://localhost:11434/api/generate", "ollamaModel": "llama3-test"}
    
    ConfigManager.save_settings(settings)
    ConfigManager.save_credentials(credentials, key="my-secret-salt", obfuscate=True)
    
    full_config = ConfigManager.get_full_config()
    assert full_config.get("selectedApi") == "ollama"
    assert full_config.get("netTimeout") == 12
    assert full_config.get("ollamaUrl") == "http://localhost:11434/api/generate"
    assert full_config.get("ollamaModel") == "llama3-test"
    assert full_config.get("encryptionKey") == "my-secret-salt"
