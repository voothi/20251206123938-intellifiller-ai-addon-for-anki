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
