import pytest
from IntelliFiller.process_notes import MultipleNotesThreadWorker, get_deck_name
from anki.notes import Note

def test_get_deck_name_fallback():
    # Verify get_deck_name handles notes without cards or collections safely
    note = "mock_note"
    assert get_deck_name(note) == "Unknown Deck"

def test_worker_successful_run(mocker):
    # Mock database retrieval and note processing
    import aqt
    mock_note = mocker.Mock(spec=Note)
    aqt.mw.col = mocker.Mock()
    aqt.mw.col.get_note.return_value = mock_note
    
    mock_enrich = mocker.patch("IntelliFiller.process_notes.enrich_without_editor")
    
    # Instantiate worker
    worker = MultipleNotesThreadWorker(notes=[123], browser=None, prompt_config={"promptName": "test"})
    worker.set_permission(True)
    
    # Mock QThread methods to avoid early termination in mocks
    worker.isInterruptionRequested = mocker.Mock(return_value=False)
    
    # Track signal emission by overriding signals on instance
    worker.progress_made = mocker.Mock()
    
    # Run synchronously in test thread
    worker.run()
    
    worker.progress_made.emit.assert_called_once_with(1)
    mock_enrich.assert_called_once_with(mock_note, {"promptName": "test"})

def test_worker_network_error_retry(mocker):
    import aqt
    mock_note = mocker.Mock(spec=Note)
    aqt.mw.col = mocker.Mock()
    aqt.mw.col.get_note.return_value = mock_note
    
    # Mock time.sleep to run instantly
    mock_sleep = mocker.patch("time.sleep")
    
    # Mock enrich_without_editor to fail first with timeout, then succeed
    mock_enrich = mocker.patch("IntelliFiller.process_notes.enrich_without_editor")
    mock_enrich.side_effect = [
        Exception("Connection timed out"),
        None
    ]
    
    worker = MultipleNotesThreadWorker(notes=[123], browser=None, prompt_config={"promptName": "test"})
    worker.set_permission(True)
    
    # Mock QThread methods to avoid early termination in mocks
    worker.isInterruptionRequested = mocker.Mock(return_value=False)
    
    # Track signal emission by overriding signals on instance
    worker.progress_made = mocker.Mock()
    worker.status_update = mocker.Mock()
    
    worker.run()
    
    # Verify that it emitted the retry status, slept, retried, and succeeded
    worker.status_update.emit.assert_any_call("Network error. Retrying...")
    mock_sleep.assert_called_once_with(3)
    worker.progress_made.emit.assert_called_once_with(1)
    assert mock_enrich.call_count == 2




