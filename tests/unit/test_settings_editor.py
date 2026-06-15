import json
import pytest
from IntelliFiller.settings_editor import SettingsWindow
from IntelliFiller.config_manager import ConfigManager

def test_settings_window_initialization():
    # Setup some starting config
    config = {
        "selectedApi": "ollama",
        "ollamaUrl": "http://localhost:11434/api/generate",
        "ollamaModel": "llama3-test",
        "ollamaCloudUrl": "https://ollama.com/api/generate",
        "ollamaCloudKey": "test-cloud-key",
        "ollamaCloudModel": "llama3-cloud-test",
        "netTimeout": 15,
        "obfuscateCreds": True,
        "encryptionKey": "test-editor-salt"
    }
    ConfigManager.save_settings({k: v for k, v in config.items() if k not in ["ollamaCloudKey"]})
    ConfigManager.save_credentials({"ollamaCloudKey": "test-cloud-key"}, key="test-editor-salt", obfuscate=True)
    
    # Instantiate SettingsWindow
    window = SettingsWindow()
    
    # Verify that the widgets got populated with the values from config
    assert window.ollamaUrl.text() == "http://localhost:11434/api/generate"
    assert window.ollamaModel.text() == "llama3-test"
    assert window.ollamaCloudUrl.text() == "https://ollama.com/api/generate"
    assert window.ollamaCloudKey.text() == "test-cloud-key"
    assert window.ollamaCloudModel.text() == "llama3-cloud-test"
    assert window.netTimeout.value() == 15
    assert window.encryptionKey.text() == "test-editor-salt"

def test_settings_window_save():
    # Setup initial config
    ConfigManager.save_settings({
        "selectedApi": "openai",
        "netTimeout": 10,
        "encryptionKey": "old-salt"
    })
    
    window = SettingsWindow()
    
    # Simulate user changing some fields in the UI
    window.selectedApi.setCurrentData("ollama_cloud")
    window.ollamaCloudUrl.setText("https://ollama-test.com/api/generate")
    window.ollamaCloudKey.setText("new-secret-key")
    window.ollamaCloudModel.setText("new-cloud-model")
    window.netTimeout.setValue(30)
    window.encryptionKey.setText("new-salt-key")
    
    # Simulate clicking OK/Save
    window.on_ok_clicked()
    
    # Reload and assert persisted values
    saved_config = ConfigManager.get_full_config()
    assert saved_config.get("selectedApi") == "ollama_cloud"
    assert saved_config.get("ollamaCloudUrl") == "https://ollama-test.com/api/generate"
    assert saved_config.get("ollamaCloudKey") == "new-secret-key"
    assert saved_config.get("ollamaCloudModel") == "new-cloud-model"
    assert saved_config.get("netTimeout") == 30
    assert saved_config.get("encryptionKey") == "new-salt-key"


@pytest.mark.security
def test_settings_save_strips_backup_password_from_plaintext_settings(mocker):
    ConfigManager.save_settings({})
    window = SettingsWindow()
    window.backupPassword.setText("plaintext-zip-pwd")
    window.on_apply_clicked()

    raw_settings = open(ConfigManager.SETTINGS_FILE, "r", encoding="utf-8").read()
    assert "plaintext-zip-pwd" not in raw_settings

    creds = ConfigManager.load_credentials()
    assert creds.get("backupZipPassword") == "plaintext-zip-pwd"


@pytest.mark.security
def test_settings_save_persists_api_keys_as_credentials_not_settings():
    ConfigManager.save_settings({})
    window = SettingsWindow()
    window.apiKey.setText("openai-secret-123")
    window.openaiModel.setText("gpt-4o")
    window.encryptionKey.setText("salt-1")
    window.on_apply_clicked()

    raw_settings = open(ConfigManager.SETTINGS_FILE, "r", encoding="utf-8").read()
    assert "openai-secret-123" not in raw_settings
    assert "gpt-4o" not in raw_settings

    creds = ConfigManager.load_credentials(key="salt-1")
    assert creds.get("apiKey") == "openai-secret-123"
    assert creds.get("openaiModel") == "gpt-4o"


@pytest.mark.security
def test_settings_save_reencrypts_when_key_changes():
    ConfigManager.save_settings({})
    window = SettingsWindow()
    window.encryptionKey.setText("old-key")
    window.apiKey.setText("rotate-me")
    window.on_apply_clicked()

    window2 = SettingsWindow()
    window2.encryptionKey.setText("new-key")
    window2.apiKey.setText("rotate-me")
    window2.on_apply_clicked()

    assert ConfigManager.load_credentials(key="new-key").get("apiKey") == "rotate-me"
    assert ConfigManager.load_credentials(key="old-key").get("apiKey", "") == ""


def test_settings_window_close_with_no_changes_closes():
    ConfigManager.save_settings({"selectedApi": "openai"})
    window = SettingsWindow()
    window.config_saved = True
    event = mocker_stub_event()
    window.closeEvent(event)
    assert event.accepted is True


def test_settings_window_close_with_unsaved_changes_discard(mocker):
    ConfigManager.save_settings({"selectedApi": "openai"})
    window = SettingsWindow()
    window.netTimeout.setValue(99)
    mocker.patch("IntelliFiller.settings_editor.QMessageBox.question",
                 return_value=window.StandardButton.Discard)
    event = mocker_stub_event()
    window.closeEvent(event)
    assert event.accepted is True


def test_settings_window_close_with_unsaved_changes_cancel(mocker):
    ConfigManager.save_settings({"selectedApi": "openai"})
    window = SettingsWindow()
    window.netTimeout.setValue(99)
    mocker.patch("IntelliFiller.settings_editor.QMessageBox.question",
                 return_value=window.StandardButton.Cancel)
    event = mocker_stub_event()
    window.closeEvent(event)
    assert event.accepted is False


def test_settings_window_close_with_unsaved_changes_save(mocker):
    ConfigManager.save_settings({"netTimeout": 10})
    window = SettingsWindow()
    window.netTimeout.setValue(77)
    mocker.patch("IntelliFiller.settings_editor.QMessageBox.question",
                 return_value=window.StandardButton.Save)
    event = mocker_stub_event()
    window.closeEvent(event)
    assert event.accepted is True
    assert ConfigManager.load_settings().get("netTimeout") == 77


def test_settings_window_on_apply_shows_info(mocker):
    mock_show = mocker.patch("IntelliFiller.settings_editor.showInfo")
    ConfigManager.save_settings({})
    window = SettingsWindow()
    window.on_apply_clicked()
    mock_show.assert_called_once()


def test_settings_window_browse_local_path_uses_dialog(mocker):
    mocker.patch("IntelliFiller.settings_editor.QFileDialog.getExistingDirectory",
                 return_value="C:/picked")
    ConfigManager.save_settings({})
    window = SettingsWindow()
    window.browse_local_path()
    assert window.backupLocalPath.text() == "C:/picked"


def test_settings_window_browse_local_path_cancel(mocker):
    mocker.patch("IntelliFiller.settings_editor.QFileDialog.getExistingDirectory",
                 return_value="")
    ConfigManager.save_settings({})
    window = SettingsWindow()
    window.backupLocalPath.setText("unchanged")
    window.browse_local_path()
    assert window.backupLocalPath.text() == "unchanged"


def mocker_stub_event():
    class _Event:
        def __init__(self):
            self.accepted = False
            self.ignored = False
        def accept(self):
            self.accepted = True
        def ignore(self):
            self.ignored = True
    return _Event()


def test_settings_window_duplicate_prompt(monkeypatch, tmp_path):
    import os
    # Set up temporary prompts dir to avoid interfering with real config
    monkeypatch.setattr(ConfigManager, "USER_FILES_DIR", str(tmp_path))
    monkeypatch.setattr(ConfigManager, "SETTINGS_FILE", os.path.join(str(tmp_path), "settings.json"))
    monkeypatch.setattr(ConfigManager, "PROMPTS_DIR", os.path.join(str(tmp_path), "prompts"))
    
    # Save a prompt first
    prompt_data = {
        "promptName": "English Translation",
        "prompt": "Translate {{{Word}}} to English",
        "targetField": "Translation",
        "pinned": True,
        "responseFormat": "text",
        "fieldMapping": {}
    }
    ConfigManager.save_prompt(prompt_data)
    ConfigManager.save_settings({"selectedApi": "openai"})

    window = SettingsWindow()
    assert len(window.prompts) == 1
    assert window.prompts[0]["promptName"] == "English Translation"

    # Mock currentRow selection
    window.promptsList.currentRow = lambda: 0

    # Click duplicate button or invoke the method directly
    window.duplicate_selected_prompt()

    # Verify a new prompt is added with " - Copy" suffix
    assert len(window.prompts) == 2
    assert window.prompts[1]["promptName"] == "English Translation - Copy"
    assert window.prompts[1]["prompt"] == "Translate {{{Word}}} to English"
    assert window.prompts[1]["targetField"] == "Translation"
    assert window.prompts[1]["pinned"] is True

    # Test duplicating again produces unique name with counter
    window.promptsList.currentRow = lambda: 1
    window.duplicate_selected_prompt()
    assert len(window.prompts) == 3
    assert window.prompts[2]["promptName"] == "English Translation - Copy - Copy"

    # Test duplicating the first one again produces "English Translation - Copy (1)"
    window.promptsList.currentRow = lambda: 0
    window.duplicate_selected_prompt()
    assert len(window.prompts) == 4
    assert window.prompts[3]["promptName"] == "English Translation - Copy (1)"



