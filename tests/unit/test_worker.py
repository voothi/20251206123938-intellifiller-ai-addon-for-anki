import pytest
from IntelliFiller.process_notes import (
    MultipleNotesThreadWorker,
    get_deck_name,
    update_history_config,
    ProgressDialog,
)
from anki.notes import Note


def test_get_deck_name_fallback():
    note = "mock_note"
    assert get_deck_name(note) == "Unknown Deck"


def test_get_deck_name_with_card(mocker):
    import aqt
    col = mocker.Mock()
    col.decks.get.return_value = {"name": "My Deck", "id": 42}
    mocker.patch.object(aqt.mw, "col", col, create=True)

    card = mocker.Mock()
    card.did = 42
    note = mocker.Mock()
    note.cards.return_value = [card]

    assert get_deck_name(note) == "My Deck"


def test_get_deck_name_card_but_missing_deck(mocker):
    import aqt
    col = mocker.Mock()
    col.decks.get.return_value = None
    mocker.patch.object(aqt.mw, "col", col, create=True)

    card = mocker.Mock()
    card.did = 999
    note = mocker.Mock()
    note.cards.return_value = [card]

    assert get_deck_name(note) == "Unknown Deck"


def test_get_deck_name_handles_exception(mocker):
    import aqt
    col = mocker.Mock()
    col.decks.get.side_effect = Exception("boom")
    mocker.patch.object(aqt.mw, "col", col, create=True)

    note = mocker.Mock()
    note.cards.return_value = [mocker.Mock()]

    assert get_deck_name(note) == "Unknown Deck"


def test_worker_successful_run(mocker):
    import aqt
    mock_note = mocker.Mock(spec=Note)
    col = mocker.Mock()
    col.get_note.return_value = mock_note
    mocker.patch.object(aqt.mw, "col", col, create=True)

    mock_enrich = mocker.patch("IntelliFiller.process_notes.enrich_without_editor")

    worker = MultipleNotesThreadWorker(notes=[123], browser=None, prompt_config={"promptName": "test"})
    worker.set_permission(True)
    worker.isInterruptionRequested = mocker.Mock(return_value=False)
    worker.progress_made = mocker.Mock()

    worker.run()

    worker.progress_made.emit.assert_called_once_with(1)
    mock_enrich.assert_called_once_with(mock_note, {"promptName": "test"})
    assert len(worker.successes) == 1
    assert worker.successes[0]["retries"] == 0
    assert worker.successes[0]["attempt_errors"] == []


def test_worker_uses_note_instance_fast_path(mocker):
    mock_note = Note()
    mock_enrich = mocker.patch("IntelliFiller.process_notes.enrich_without_editor")

    worker = MultipleNotesThreadWorker(notes=[mock_note], browser=None, prompt_config={"promptName": "test"})
    worker.set_permission(True)
    worker.isInterruptionRequested = mocker.Mock(return_value=False)
    worker.progress_made = mocker.Mock()

    worker.run()

    mock_enrich.assert_called_once_with(mock_note, {"promptName": "test"})


def test_worker_skips_note_when_get_note_raises(mocker):
    import aqt
    col = mocker.Mock()
    col.get_note.side_effect = Exception("note deleted")
    mocker.patch.object(aqt.mw, "col", col, create=True)

    worker = MultipleNotesThreadWorker(notes=[999], browser=None, prompt_config={"promptName": "test"})
    worker.set_permission(True)
    worker.isInterruptionRequested = mocker.Mock(return_value=False)
    worker.progress_made = mocker.Mock()

    worker.run()

    worker.progress_made.emit.assert_called_once_with(1)
    assert len(worker.skips) == 1
    assert worker.skips[0]["attempt_errors"] == ["Note deleted or not found"]


def test_worker_network_error_retry(mocker):
    import aqt
    mock_note = mocker.Mock(spec=Note)
    col = mocker.Mock()
    col.get_note.return_value = mock_note
    mocker.patch.object(aqt.mw, "col", col, create=True)

    mock_sleep = mocker.patch("time.sleep")

    mock_enrich = mocker.patch("IntelliFiller.process_notes.enrich_without_editor")
    mock_enrich.side_effect = [
        Exception("Connection timed out"),
        None,
    ]

    worker = MultipleNotesThreadWorker(notes=[123], browser=None, prompt_config={"promptName": "test"})
    worker.set_permission(True)
    worker.isInterruptionRequested = mocker.Mock(return_value=False)
    worker.progress_made = mocker.Mock()
    worker.status_update = mocker.Mock()

    worker.run()

    worker.status_update.emit.assert_any_call("Network error. Retrying...")
    mock_sleep.assert_called_once_with(3)
    worker.progress_made.emit.assert_called_once_with(1)
    assert mock_enrich.call_count == 2
    assert len(worker.successes) == 1
    assert worker.successes[0]["retries"] == 1
    assert worker.successes[0]["attempt_errors"] == ["Connection timed out"]


def test_worker_non_network_error_skips_after_one_attempt(mocker):
    import aqt
    mock_note = mocker.Mock(spec=Note)
    col = mocker.Mock()
    col.get_note.return_value = mock_note
    mocker.patch.object(aqt.mw, "col", col, create=True)

    mock_sleep = mocker.patch("time.sleep")
    mock_enrich = mocker.patch("IntelliFiller.process_notes.enrich_without_editor")
    mock_enrich.side_effect = ValueError("template malformed")

    worker = MultipleNotesThreadWorker(notes=[123], browser=None, prompt_config={"promptName": "test"})
    worker.set_permission(True)
    worker.isInterruptionRequested = mocker.Mock(return_value=False)
    worker.progress_made = mocker.Mock()
    worker.status_update = mocker.Mock()

    worker.run()

    assert mock_enrich.call_count == 1
    mock_sleep.assert_not_called()
    worker.progress_made.emit.assert_called_once_with(1)
    assert len(worker.skips) == 1
    assert worker.skips[0]["attempt_errors"] == ["template malformed"]


def test_worker_interruption_exits_immediately(mocker):
    mock_enrich = mocker.patch("IntelliFiller.process_notes.enrich_without_editor")

    worker = MultipleNotesThreadWorker(notes=[1, 2, 3], browser=None, prompt_config={"promptName": "test"})
    worker.set_permission(True)
    worker.isInterruptionRequested = mocker.Mock(return_value=True)
    worker.progress_made = mocker.Mock()

    worker.run()

    mock_enrich.assert_not_called()
    worker.progress_made.emit.assert_not_called()


def test_update_history_config_adds_new_item():
    from IntelliFiller.config_manager import ConfigManager
    ConfigManager._ensure_directories()
    ConfigManager.save_settings({"history": ["OldOne"]})
    update_history_config("NewOne")
    loaded = ConfigManager.load_settings()
    assert loaded["history"][0] == "NewOne"
    assert "OldOne" in loaded["history"]


def test_update_history_config_moves_existing_to_front():
    from IntelliFiller.config_manager import ConfigManager
    ConfigManager._ensure_directories()
    ConfigManager.save_settings({"history": ["A", "B", "C"]})
    update_history_config("C")
    loaded = ConfigManager.load_settings()
    assert loaded["history"][0] == "C"
    assert loaded["history"].count("C") == 1


def test_update_history_config_caps_at_20():
    from IntelliFiller.config_manager import ConfigManager
    ConfigManager._ensure_directories()
    ConfigManager.save_settings({})
    for i in range(25):
        update_history_config(f"item-{i}")
    loaded = ConfigManager.load_settings()
    assert len(loaded["history"]) == 20
    assert loaded["history"][0] == "item-24"


def test_progress_dialog_summary_always_show(mocker):
    import aqt
    # Mock ConfigManager settings
    mocker.patch("IntelliFiller.process_notes.ConfigManager.load_settings", return_value={"alwaysShowSummary": True})
    
    # Mock SummaryDialog
    mock_summary_dialog = mocker.patch("IntelliFiller.process_notes.SummaryDialog")
    
    # Mock execution manager
    mocker.patch("IntelliFiller.process_notes.ExecutionManager.instance")
    
    # Mock mw
    mocker.patch("IntelliFiller.process_notes.mw")
    
    # Mock ProgressDialog methods and init
    mocker.patch("IntelliFiller.process_notes.QDialog.__init__", return_value=None)
    mocker.patch("IntelliFiller.process_notes.QProgressBar")
    mocker.patch("IntelliFiller.process_notes.QLabel")
    mocker.patch("IntelliFiller.process_notes.QLineEdit")
    mocker.patch("IntelliFiller.process_notes.QPushButton")
    mocker.patch("IntelliFiller.process_notes.QVBoxLayout")
    mocker.patch("IntelliFiller.process_notes.QHBoxLayout")
    
    dialog = ProgressDialog()
    dialog.worker = mocker.Mock()
    dialog.worker.get_summary.return_value = {
        "successes": [],
        "skips": [],
        "json_failures": [],
        "network_failures": []
    }
    dialog.worker.prompt_config = {}
    dialog.progress_bar = mocker.Mock()
    dialog.progress_bar.maximum.return_value = 10
    dialog.update_progress = mocker.Mock()
    dialog.watchdog_timer = mocker.Mock()
    dialog.close = mocker.Mock()
    dialog.parent = mocker.Mock(return_value=None)
    
    dialog.on_worker_finished()
    
    mock_summary_dialog.assert_called_once()
    mock_summary_dialog.return_value.exec.assert_called_once()


def test_progress_dialog_summary_no_show_without_errors(mocker):
    import aqt
    mocker.patch("IntelliFiller.process_notes.ConfigManager.load_settings", return_value={"alwaysShowSummary": False})
    mock_summary_dialog = mocker.patch("IntelliFiller.process_notes.SummaryDialog")
    mocker.patch("IntelliFiller.process_notes.ExecutionManager.instance")
    mocker.patch("IntelliFiller.process_notes.mw")
    mocker.patch("IntelliFiller.process_notes.QDialog.__init__", return_value=None)
    
    dialog = ProgressDialog()
    dialog.worker = mocker.Mock()
    dialog.worker.get_summary.return_value = {
        "successes": [{"note_id": 123}],
        "skips": [],
        "json_failures": [],
        "network_failures": []
    }
    dialog.worker.prompt_config = {}
    dialog.progress_bar = mocker.Mock()
    dialog.progress_bar.maximum.return_value = 10
    dialog.update_progress = mocker.Mock()
    dialog.watchdog_timer = mocker.Mock()
    dialog.close = mocker.Mock()
    dialog.parent = mocker.Mock(return_value=None)
    
    dialog.on_worker_finished()
    
    mock_summary_dialog.assert_not_called()


def test_progress_dialog_summary_show_on_errors(mocker):
    import aqt
    mocker.patch("IntelliFiller.process_notes.ConfigManager.load_settings", return_value={"alwaysShowSummary": False})
    mock_summary_dialog = mocker.patch("IntelliFiller.process_notes.SummaryDialog")
    mocker.patch("IntelliFiller.process_notes.ExecutionManager.instance")
    mocker.patch("IntelliFiller.process_notes.mw")
    mocker.patch("IntelliFiller.process_notes.QDialog.__init__", return_value=None)
    
    dialog = ProgressDialog()
    dialog.worker = mocker.Mock()
    dialog.worker.get_summary.return_value = {
        "successes": [],
        "skips": [{"note_id": 123, "reason": "skip"}],
        "json_failures": [],
        "network_failures": []
    }
    dialog.worker.prompt_config = {}
    dialog.progress_bar = mocker.Mock()
    dialog.progress_bar.maximum.return_value = 10
    dialog.update_progress = mocker.Mock()
    dialog.watchdog_timer = mocker.Mock()
    dialog.close = mocker.Mock()
    dialog.parent = mocker.Mock(return_value=None)
    
    dialog.on_worker_finished()
    
    mock_summary_dialog.assert_called_once()
    mock_summary_dialog.return_value.exec.assert_called_once()


def test_worker_network_error_endless_retry(mocker):
    import aqt
    mock_note = mocker.Mock(spec=Note)
    col = mocker.Mock()
    col.get_note.return_value = mock_note
    mocker.patch.object(aqt.mw, "col", col, create=True)
    mocker.patch("time.sleep")
    
    mocker.patch("IntelliFiller.process_notes.ConfigManager.load_settings", return_value={"maxNetworkRetries": -1})
    
    mock_enrich = mocker.patch("IntelliFiller.process_notes.enrich_without_editor")
    # Raise error 5 times, then succeed
    mock_enrich.side_effect = [
        Exception("Connection timed out"),
        Exception("Connection timed out"),
        Exception("Connection timed out"),
        Exception("Connection timed out"),
        Exception("Connection timed out"),
        None,
    ]
    
    worker = MultipleNotesThreadWorker(notes=[123], browser=None, prompt_config={"promptName": "test"})
    worker.set_permission(True)
    worker.isInterruptionRequested = mocker.Mock(return_value=False)
    worker.progress_made = mocker.Mock()
    worker.status_update = mocker.Mock()
    
    worker.run()
    
    assert mock_enrich.call_count == 6
    assert len(worker.network_failures) == 0
    assert len(worker.successes) == 1
    assert worker.successes[0]["attempt_errors"] == ["Connection timed out"] * 5


def test_worker_network_error_limited_retry(mocker):
    import aqt
    mock_note = mocker.Mock(spec=Note)
    col = mocker.Mock()
    col.get_note.return_value = mock_note
    mocker.patch.object(aqt.mw, "col", col, create=True)
    mocker.patch("time.sleep")
    
    mocker.patch("IntelliFiller.process_notes.ConfigManager.load_settings", return_value={"maxNetworkRetries": 2})
    
    mock_enrich = mocker.patch("IntelliFiller.process_notes.enrich_without_editor")
    # Limit is 2. So 3rd failure should trigger break.
    mock_enrich.side_effect = [
        Exception("Connection timed out"), # retry 1
        Exception("Connection timed out"), # retry 2
        Exception("Connection timed out"), # retry 3 -> break
        None,
    ]
    
    worker = MultipleNotesThreadWorker(notes=[123], browser=None, prompt_config={"promptName": "test"})
    worker.set_permission(True)
    worker.isInterruptionRequested = mocker.Mock(return_value=False)
    worker.progress_made = mocker.Mock()
    worker.status_update = mocker.Mock()
    
    worker.run()
    
    # 3 failures, since limit of retries is 2, it fails on the 3rd attempt's error (which is retry 3)
    assert mock_enrich.call_count == 3
    assert len(worker.network_failures) == 1
    assert worker.network_failures[0]["retries"] == 3
    assert worker.network_failures[0]["attempt_errors"] == ["Connection timed out"] * 3
    assert len(worker.successes) == 0


def test_worker_network_error_zero_retry(mocker):
    import aqt
    mock_note = mocker.Mock(spec=Note)
    col = mocker.Mock()
    col.get_note.return_value = mock_note
    mocker.patch.object(aqt.mw, "col", col, create=True)
    mocker.patch("time.sleep")
    
    mocker.patch("IntelliFiller.process_notes.ConfigManager.load_settings", return_value={"maxNetworkRetries": 0})
    
    mock_enrich = mocker.patch("IntelliFiller.process_notes.enrich_without_editor")
    # Limit is 0. So 1st failure should trigger break immediately.
    mock_enrich.side_effect = [
        Exception("Connection timed out"),
        None,
    ]
    
    worker = MultipleNotesThreadWorker(notes=[123], browser=None, prompt_config={"promptName": "test"})
    worker.set_permission(True)
    worker.isInterruptionRequested = mocker.Mock(return_value=False)
    worker.progress_made = mocker.Mock()
    worker.status_update = mocker.Mock()
    
    worker.run()
    
    assert mock_enrich.call_count == 1
    assert len(worker.network_failures) == 1
    assert worker.network_failures[0]["retries"] == 1
    assert worker.network_failures[0]["attempt_errors"] == ["Connection timed out"]
    assert len(worker.successes) == 0


def test_summary_dialog_tab_selection(mocker):
    # Mock Qt classes used in SummaryDialog.__init__
    mocker.patch("IntelliFiller.process_notes.QDialog.__init__", return_value=None)
    mocker.patch("IntelliFiller.process_notes.QVBoxLayout")
    mocker.patch("IntelliFiller.process_notes.QHBoxLayout")
    mocker.patch("IntelliFiller.process_notes.QLabel")
    mocker.patch("IntelliFiller.process_notes.QPushButton")
    mocker.patch("IntelliFiller.process_notes.QDialog.resize")
    mocker.patch("IntelliFiller.process_notes.QDialog.setWindowTitle")
    mocker.patch("IntelliFiller.process_notes.QDialog.setLayout")
    
    mock_tabs = mocker.patch("IntelliFiller.process_notes.QTabWidget")
    mocker.patch("IntelliFiller.process_notes.SummaryDialog._build_table")
    
    from IntelliFiller.process_notes import SummaryDialog
    
    # Case 1: No errors
    summary_no_errors = {
        "total": 10,
        "successes": [{"note_id": 1}],
        "skips": [],
        "json_failures": [],
        "network_failures": []
    }
    
    dialog = SummaryDialog(parent=None, summary=summary_no_errors, prompt_config={})
    # Since there are no errors, setCurrentIndex should NOT be called
    mock_tabs.return_value.setCurrentIndex.assert_not_called()
    
    # Case 2: Errors exist
    summary_with_errors = {
        "total": 10,
        "successes": [],
        "skips": [{"note_id": 2, "reason": "some error"}],
        "json_failures": [],
        "network_failures": []
    }
    
    # Reset mock
    mock_tabs.return_value.setCurrentIndex.reset_mock()
    
    dialog2 = SummaryDialog(parent=None, summary=summary_with_errors, prompt_config={})
    # Since there are errors, setCurrentIndex should be called with 1 (All Failures tab)
    mock_tabs.return_value.setCurrentIndex.assert_called_once_with(1)



