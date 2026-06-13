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

def test_migrate_legacy_config(mocker):
    # Mock mw.addonManager.getConfig
    import aqt
    aqt.mw.addonManager.getConfig = mocker.Mock(return_value={
        "apiKey": "legacy-openai-key",
        "netTimeout": 42,
        "prompts": [{"promptName": "LegacyPrompt", "prompt": "Translate {{{Word}}}"}]
    })
    
    # Run migration
    ConfigManager.migrate_legacy_config("IntelliFiller")
    
    # Assert settings were saved
    settings = ConfigManager.load_settings()
    assert settings.get("netTimeout") == 42
    
    # Assert credentials were saved (migrated to user_files/credentials.json)
    creds = ConfigManager.load_credentials()
    assert creds.get("apiKey") == "legacy-openai-key"
    
    # Assert prompts were saved
    prompts = ConfigManager.list_prompts()
    assert len(prompts) == 1
    assert prompts[0]["promptName"] == "LegacyPrompt"

def test_legacy_secrets_detection_and_sanitization():
    # Create dummy meta.json and config.json inside the mocked addon dir
    meta_path = os.path.join(ConfigManager.ADDON_DIR, "meta.json")
    config_path = os.path.join(ConfigManager.ADDON_DIR, "config.json")
    
    import json
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"config": {"apiKey": "secret-key", "netTimeout": 10}}, f)
        
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump({"apiKey": "secret-key", "other": "val"}, f)
        
    # Check secrets exist
    assert ConfigManager.has_legacy_secrets("IntelliFiller") is True
    
    # Sanitize
    ConfigManager.sanitize_legacy_files("IntelliFiller")
    
    # Check secrets are gone
    assert ConfigManager.has_legacy_secrets("IntelliFiller") is False
    
    with open(meta_path, "r", encoding="utf-8") as f:
        meta_data = json.load(f)
        assert meta_data["config"]["apiKey"] == ""
        assert meta_data["config"]["netTimeout"] == 10
        
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
        assert config_data["apiKey"] == ""


def test_save_and_load_prompt():
    prompt = {
        "promptName": "Test Prompt",
        "prompt": "Translate {{{Word}}}",
        "targetField": "Translation",
        "responseFormat": "text"
    }
    ConfigManager.save_prompt(prompt)
    
    loaded = ConfigManager.list_prompts()
    assert any(p["promptName"] == "Test Prompt" for p in loaded)
    
    ConfigManager.delete_prompt_file("Test Prompt")
    assert not any(p["promptName"] == "Test Prompt" for p in ConfigManager.list_prompts())
