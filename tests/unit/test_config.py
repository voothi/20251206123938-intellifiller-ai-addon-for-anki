import os
from IntelliFiller.config_manager import ConfigManager

def test_default_config():
    config = ConfigManager.get_full_config()
    assert isinstance(config, dict)
    assert config.get("prompts") == []


def test_migrate_legacy_skips_when_already_migrated(mocker):
    import aqt
    ConfigManager.save_settings({"already": True, "netTimeout": 7})
    mocker.patch.object(
        aqt.mw.addonManager, "getConfig",
        return_value={"apiKey": "should-not-be-picked-up", "netTimeout": 999},
    )
    ConfigManager.migrate_legacy_config("IntelliFiller")
    settings = ConfigManager.load_settings()
    assert settings.get("already") is True
    assert settings.get("netTimeout") == 7
    assert not ConfigManager.list_prompts()


def test_migrate_legacy_no_legacy_config_returns_early(mocker):
    import aqt
    mocker.patch.object(aqt.mw.addonManager, "getConfig", return_value=None)
    ConfigManager.migrate_legacy_config("IntelliFiller")
    assert not os.path.exists(ConfigManager.SETTINGS_FILE)
    assert not os.path.exists(ConfigManager.CREDENTIALS_FILE)

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
    mocker.patch.object(aqt.mw.addonManager, "getConfig", return_value={
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
        assert config_data["other"] == "val"


def test_legacy_sanitize_idempotent_when_no_secrets():
    meta_path = os.path.join(ConfigManager.ADDON_DIR, "meta.json")
    config_path = os.path.join(ConfigManager.ADDON_DIR, "config.json")

    import json
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"config": {"apiKey": "", "netTimeout": 12}}, f)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump({"netTimeout": 12, "other": "val"}, f)

    assert ConfigManager.has_legacy_secrets("IntelliFiller") is False
    ConfigManager.sanitize_legacy_files("IntelliFiller")
    assert ConfigManager.has_legacy_secrets("IntelliFiller") is False
    with open(meta_path, "r", encoding="utf-8") as f:
        assert json.load(f)["config"]["netTimeout"] == 12


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


def test_xor_cipher_roundtrip():
    plain = "hello world"
    key = "k"
    cipher = ConfigManager._xor_cipher(plain, key)
    assert cipher != plain
    assert ConfigManager._xor_cipher(cipher, key) == plain


def test_xor_cipher_unicode_roundtrip():
    plain = "café — naïve, résumé"
    key = "salt"
    cipher = ConfigManager._xor_cipher(plain, key)
    assert ConfigManager._xor_cipher(cipher, key) == plain


def test_xor_cipher_empty_string():
    assert ConfigManager._xor_cipher("", "any") == ""


def test_credentials_obfuscation_hides_plaintext(tmp_path, monkeypatch):
    monkeypatch.setattr(ConfigManager, "CREDENTIALS_FILE", os.path.join(str(tmp_path), "creds.json"))
    secret = "super-secret-api-key-1234"
    ConfigManager.save_credentials({"apiKey": secret}, obfuscate=True)
    raw = open(ConfigManager.CREDENTIALS_FILE, "r", encoding="utf-8").read()
    assert secret not in raw
    assert raw  # file is non-empty
    assert ConfigManager.load_credentials() == {"apiKey": secret}


def test_credentials_plain_mode_writes_json(tmp_path, monkeypatch):
    monkeypatch.setattr(ConfigManager, "CREDENTIALS_FILE", os.path.join(str(tmp_path), "creds.json"))
    ConfigManager.save_credentials({"apiKey": "plain-key"}, obfuscate=False)
    raw = open(ConfigManager.CREDENTIALS_FILE, "r", encoding="utf-8").read()
    assert "plain-key" in raw
    assert ConfigManager.load_credentials() == {"apiKey": "plain-key"}


def test_credentials_load_returns_empty_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(ConfigManager, "CREDENTIALS_FILE", os.path.join(str(tmp_path), "missing.json"))
    assert ConfigManager.load_credentials() == {}


def test_credentials_load_falls_back_to_plain_on_corruption(tmp_path, monkeypatch):
    monkeypatch.setattr(ConfigManager, "CREDENTIALS_FILE", os.path.join(str(tmp_path), "bad.json"))
    with open(ConfigManager.CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        f.write("this is not base64 or json at all !!!")
    assert ConfigManager.load_credentials() == {}


def test_write_file_safely_overwrites_existing(tmp_path):
    path = os.path.join(str(tmp_path), "f.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write("OLD")
    ConfigManager._write_file_safely(path, "NEW")
    with open(path, "r", encoding="utf-8") as f:
        assert f.read() == "NEW"
    assert not os.path.exists(path + ".tmp")


def test_write_file_safely_creates_when_missing(tmp_path):
    path = os.path.join(str(tmp_path), "fresh.json")
    ConfigManager._write_file_safely(path, "DATA")
    with open(path, "r", encoding="utf-8") as f:
        assert f.read() == "DATA"


def test_write_file_safely_cleans_tmp_on_failure(tmp_path, monkeypatch):
    path = os.path.join(str(tmp_path), "boom.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write("EXISTING")

    real_replace = os.replace

    def boom_replace(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", boom_replace)
    try:
        try:
            ConfigManager._write_file_safely(path, "NEW")
        except OSError:
            pass
        assert not os.path.exists(path + ".tmp")
    finally:
        monkeypatch.setattr(os, "replace", real_replace)
    with open(path, "r", encoding="utf-8") as f:
        assert f.read() == "EXISTING"


def test_get_full_config_maps_backup_zip_password_from_credentials():
    ConfigManager.save_settings({})
    ConfigManager.save_credentials(
        {"backupZipPassword": "secret-zip-pwd", "apiKey": "x"},
        obfuscate=True,
    )
    full = ConfigManager.get_full_config()
    assert full.get("backup", {}).get("zipPassword") == "secret-zip-pwd"
    assert full.get("apiKey") == "x"


def test_list_prompts_handles_list_and_dict_shapes(tmp_path, monkeypatch):
    monkeypatch.setattr(ConfigManager, "PROMPTS_DIR", os.path.join(str(tmp_path), "prompts"))
    ConfigManager._ensure_directories()
    import json
    with open(os.path.join(ConfigManager.PROMPTS_DIR, "pack.json"), "w", encoding="utf-8") as f:
        json.dump([{"promptName": "P1"}, {"promptName": "P2"}], f)
    with open(os.path.join(ConfigManager.PROMPTS_DIR, "single.json"), "w", encoding="utf-8") as f:
        json.dump({"promptName": "P3"}, f)
    names = sorted(p["promptName"] for p in ConfigManager.list_prompts())
    assert names == ["P1", "P2", "P3"]


def test_list_prompts_skips_corrupt_files(tmp_path, monkeypatch):
    monkeypatch.setattr(ConfigManager, "PROMPTS_DIR", os.path.join(str(tmp_path), "prompts"))
    ConfigManager._ensure_directories()
    import json
    with open(os.path.join(ConfigManager.PROMPTS_DIR, "good.json"), "w", encoding="utf-8") as f:
        json.dump({"promptName": "Good"}, f)
    with open(os.path.join(ConfigManager.PROMPTS_DIR, "bad.json"), "w", encoding="utf-8") as f:
        f.write("not valid json")
    assert [p["promptName"] for p in ConfigManager.list_prompts() if p.get("promptName") == "Good"] == ["Good"]
