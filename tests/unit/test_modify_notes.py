import pytest
from IntelliFiller.modify_notes import (
    format_response_and_fill_field,
    fill_field_for_note_in_editor,
    fill_field_for_note_not_in_editor
)

def test_format_response_and_fill_field_none():
    note = {"Target": "existing"}
    format_response_and_fill_field(None, note, "Target", overwrite=True)
    assert note["Target"] == "existing"

def test_format_response_and_fill_field_not_found():
    note = {"OtherField": "value"}
    with pytest.raises(ValueError) as excinfo:
        format_response_and_fill_field("response", note, "Target", overwrite=True)
    assert "Target field 'Target' not found in note" in str(excinfo.value)

def test_format_response_and_fill_field_overwrite():
    note = {"Target": "old content"}
    format_response_and_fill_field("new\ncontent", note, "Target", overwrite=True)
    assert note["Target"] == "new<br>content"

def test_format_response_and_fill_field_no_overwrite_empty():
    note = {"Target": "   "}
    format_response_and_fill_field("new\ncontent", note, "Target", overwrite=False)
    # Strip on target existing is checked. Since existing_content.strip() is False, it should just assign new
    assert note["Target"] == "new<br>content"

def test_format_response_and_fill_field_no_overwrite_existing():
    note = {"Target": "old content"}
    format_response_and_fill_field("new\ncontent", note, "Target", overwrite=False)
    assert note["Target"] == "old content<hr>new<br>content"

def test_fill_field_for_note_in_editor(mocker):
    mock_editor = mocker.Mock()
    mock_editor.note = {"Target": "existing"}
    mock_editor.loadNoteKeepingFocus = mocker.Mock()
    
    fill_field_for_note_in_editor("new response", "Target", mock_editor, overwrite=True)
    
    assert mock_editor.note["Target"] == "new response"
    mock_editor.loadNoteKeepingFocus.assert_called_once()

def test_fill_field_for_note_not_in_editor(mocker):
    class MockNote(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.flush = mocker.Mock()
            
    mock_note = MockNote({"Target": "existing"})
    
    fill_field_for_note_not_in_editor("new response", mock_note, "Target", overwrite=True)
    
    assert mock_note["Target"] == "new response"
    mock_note.flush.assert_called_once()


def test_format_response_and_fill_field_html_escaping():
    note = {"Target": "existing"}
    format_response_and_fill_field("a < b & c > d", note, "Target", overwrite=True)
    assert note["Target"] == "a < b & c > d"
