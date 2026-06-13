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


def test_apply_response_to_note_json_invalid_raises():
    note = {}
    prompt_config = {
        "responseFormat": "json",
        "promptName": "MyPrompt",
        "fieldMapping": {"key1": "FieldA"}
    }

    with pytest.raises(ValueError) as excinfo:
        apply_response_to_note(note, prompt_config, "not json", is_editor=False)
    assert "Failed to parse JSON response" in str(excinfo.value)
    assert "MyPrompt" in str(excinfo.value)

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


def test_create_prompt_missing_field_raises():
    class MockNote(dict):
        pass

    note = MockNote({"Word": "apple"})
    config = {"prompt": "Define {{{MissingField}}}"}

    with pytest.raises(ValueError) as excinfo:
        create_prompt(note, config)
    assert "MissingField" in str(excinfo.value)


def test_create_prompt_preserves_text_without_html_tags():
    class MockNote(dict):
        pass

    note = MockNote({"Word": "apple orange"})
    config = {"prompt": "Define {{{Word}}}"}
    assert create_prompt(note, config) == "Define apple orange"


def test_create_prompt_repeats_same_placeholder():
    class MockNote(dict):
        pass

    note = MockNote({"Word": "x"})
    config = {"prompt": "{{{Word}}} and {{{Word}}}"}
    assert create_prompt(note, config) == "x and x"


def test_parse_llm_json_none_returns_none():
    assert parse_llm_json(None) is None


def test_parse_llm_json_empty_returns_none():
    assert parse_llm_json("") is None


def test_parse_llm_json_nested_object():
    payload = '{"a": {"b": 1, "c": [1, 2]}}'
    assert parse_llm_json(payload) == {"a": {"b": 1, "c": [1, 2]}}


def test_parse_llm_json_unicode_keys_and_values():
    payload = '{"café": "naïve — résumé"}'
    assert parse_llm_json(payload) == {"café": "naïve — résumé"}


def test_parse_llm_json_escaped_quotes_in_string():
    payload = '{"k": "he said \\"hi\\""}'
    assert parse_llm_json(payload) == {"k": 'he said "hi"'}


def test_parse_llm_json_fenced_with_language_tag():
    assert parse_llm_json("```JSON\n{\"a\": 1}\n```") == {"a": 1}


def test_parse_llm_json_braces_fallback_extracts_inner_object():
    text = "noise before {\"k\": \"v\"} noise after"
    assert parse_llm_json(text) == {"k": "v"}


def test_parse_llm_json_no_braces_returns_none():
    assert parse_llm_json("nothing parseable here") is None


def test_enrich_without_editor_uses_note_directly(mocker):
    from IntelliFiller.process_notes import enrich_without_editor

    note = Note()
    note.__setitem__("Word", "apple") if hasattr(note, "__setitem__") else setattr(note, "Word", "apple")

    mock_create = mocker.patch("IntelliFiller.process_notes.create_prompt", return_value="P")
    mock_send = mocker.patch("IntelliFiller.process_notes.send_prompt_to_llm", return_value="R")
    mock_apply = mocker.patch("IntelliFiller.process_notes.apply_response_to_note")

    config = {"promptName": "X", "responseFormat": "text", "targetField": "T"}
    enrich_without_editor(note, config)

    mock_create.assert_called_once_with(note, config)
    mock_send.assert_called_once_with("P")
    mock_apply.assert_called_once_with(note, config, "R", is_editor=False)


def test_enrich_without_editor_fetches_by_id(mocker):
    from IntelliFiller.process_notes import enrich_without_editor
    import aqt

    fake_note = mocker.Mock()
    col = mocker.Mock()
    col.get_note.return_value = fake_note
    mocker.patch.object(aqt.mw, "col", col, create=True)

    mock_create = mocker.patch("IntelliFiller.process_notes.create_prompt", return_value="P")
    mock_send = mocker.patch("IntelliFiller.process_notes.send_prompt_to_llm", return_value="R")
    mock_apply = mocker.patch("IntelliFiller.process_notes.apply_response_to_note")

    enrich_without_editor(12345, {"promptName": "X"})

    aqt.mw.col.get_note.assert_called_once_with(12345)
    mock_create.assert_called_once_with(fake_note, {"promptName": "X"})
    mock_apply.assert_called_once_with(fake_note, {"promptName": "X"}, "R", is_editor=False)
