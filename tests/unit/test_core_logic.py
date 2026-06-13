import pytest
from IntelliFiller.data_request import create_prompt
from IntelliFiller.process_notes import parse_llm_json, apply_response_to_note
from IntelliFiller.backup_manager import BackupManager
from IntelliFiller.config_manager import ConfigManager
from anki.notes import Note
import json
import os

def test_create_prompt():
    # Mock note with dictionary access
    class MockNote(dict):
        pass

    note = MockNote({
        "Word": "<b>apple &amp; orange</b>",
        "Translation": "Apfel"
    })

    # Test basic placeholder replacement and HTML cleaning
    config = {"prompt": "Define {{{Word}}} in German (e.g. {{{Translation}}})"}
    prompt = create_prompt(note, config)
    
    # "<b>apple &amp; orange</b>" -> unescaped: "<b>apple & orange</b>" -> tags removed: "apple & orange"
    assert prompt == "Define apple & orange in German (e.g. Apfel)"

def test_parse_llm_json():
    # Test raw valid JSON
    assert parse_llm_json('{"key": "value"}') == {"key": "value"}
    
    # Test JSON inside markdown code blocks
    assert parse_llm_json('```json\n{"key": "value"}\n```') == {"key": "value"}
    assert parse_llm_json('```\n{"key": "value"}\n```') == {"key": "value"}
    
    # Test JSON with surrounding text (braces fallback)
    assert parse_llm_json('Here is the result:\n{\n  "key": "value"\n}\nHope this helps!') == {"key": "value"}
    
    # Test invalid JSON returns None
    assert parse_llm_json('invalid json { key: val }') is None

def test_apply_response_to_note_text_mode(mocker):
    # Mock note
    note = mocker.Mock()
    mock_fill_not_editor = mocker.patch("IntelliFiller.process_notes.fill_field_for_note_not_in_editor")
    
    prompt_config = {
        "responseFormat": "text",
        "targetField": "TargetField",
        "overwriteField": True
    }
    
    apply_response_to_note(note, prompt_config, "AI response text", is_editor=False)
    
    mock_fill_not_editor.assert_called_once_with("AI response text", note, "TargetField", True)

def test_apply_response_to_note_json_mode(mocker):
    note = mocker.Mock()
    mock_fill_not_editor = mocker.patch("IntelliFiller.process_notes.fill_field_for_note_not_in_editor")
    
    prompt_config = {
        "responseFormat": "json",
        "fieldMapping": {
            "key1": "FieldA",
            "key2": "FieldB"
        },
        "overwriteField": False
    }
    
    # Response contains string and a list (which should be serialized to string)
    response_json = '{"key1": "val1", "key2": ["item1", "item2"]}'
    
    apply_response_to_note(note, prompt_config, response_json, is_editor=False)
    
    assert mock_fill_not_editor.call_count == 2
    mock_fill_not_editor.assert_any_call("val1", note, "FieldA", False)
    
    # Lists must be dumped back to JSON strings
    mock_fill_not_editor.assert_any_call('["item1", "item2"]', note, "FieldB", False)

def test_backup_manager_creation(mocker, tmp_path):
    # Setup temporary directories
    addon_dir = str(tmp_path / "addon")
    user_files_dir = os.path.join(addon_dir, "user_files")
    os.makedirs(user_files_dir, exist_ok=True)
    
    # Create some dummy files to back up
    with open(os.path.join(user_files_dir, "dummy.json"), "w", encoding="utf-8") as f:
        f.write('{"key": "value"}')
        
    mock_config_manager = mocker.Mock()
    # Mock settings returned by get_full_config
    local_path = os.path.join(str(tmp_path), "backups")
    mock_config_manager.get_full_config.return_value = {
        "backup": {
            "enabled": True,
            "localPath": local_path,
            "zipPassword": "my-pass",
            "keepDaily": 5,
            "keepHourly": 5
        }
    }
    mock_config_manager.load_settings.return_value = {}
    
    # Mock pyzipper AESZipFile to create a blank file so prune_backups has a zip file
    def mock_aes_zipfile(file_path, *args, **kwargs):
        with open(file_path, 'wb') as f:
            pass
        return mocker.MagicMock()
        
    mock_zip = mocker.patch("pyzipper.AESZipFile", side_effect=mock_aes_zipfile)
    
    # Instantiate BackupManager
    bm = BackupManager(mock_config_manager, addon_dir)
    
    # Run backup
    bm.perform_backup(force=True, backup_type='manual')
    
    # Check that a backup zip was created
    assert os.path.exists(local_path)
    zips = [f for f in os.listdir(local_path) if f.endswith(".zip")]
    assert len(zips) == 1
    assert "manual" in zips[0]
    mock_zip.assert_called_once()
