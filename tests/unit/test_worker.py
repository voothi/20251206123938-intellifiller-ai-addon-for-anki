import pytest
from IntelliFiller.process_notes import (
    MultipleNotesThreadWorker,
    get_deck_name,
    update_history_config,
)
from anki.notes import Note


def test_get_deck_name_fallback():
    note = "mock_note"
    assert get_deck_name(note) == "Unknown Deck"


def test_get_deck_name_with_card(mocker):
    import aqt
    card = mocker.Mock()
    card.did = 42
    aqt.mw.col = mocker.Mock()
    aqt.mw.col.decks.get.return_value = {"name": "My Deck", "id": 42}

    note = mocker.Mock()
    note.cards.return_value = [card]

    assert get_deck_name(note) == "My Deck"


def test_get_deck_name_card_but_missing_deck(mocker):
    import aqt
    card = mocker.Mock()
    card.did = 999
    aqt.mw.col = mocker.Mock()
    aqt.mw.col.decks.get.return_value = None

    note = mocker.Mock()
    note.cards.return_value = [card]

    assert get_deck_name(note) == "Unknown Deck"


def test_get_deck_name_handles_exception(mocker):
    import aqt
    aqt.mw.col = mocker.Mock()
    aqt.mw.col.decks.get.side_effect = Exception("boom")

    note = mocker.Mock()
    note.cards.return_value = [mocker.Mock()]

    assert get_deck_name(note) == "Unknown Deck"


def test_worker_successful_run(mocker):
    import aqt
    mock_note = mocker.Mock(spec=Note)
    aqt.mw.col = mocker.Mock()
    aqt.mw.col.get_note.return_value = mock_note

    mock_enrich = mocker.patch("IntelliFiller.process_notes.enrich_without_editor")

    worker = MultipleNotesThreadWorker(notes=[123], browser=None, prompt_config={"promptName": "test"})
    worker.set_permission(True)
    worker.isInterruptionRequested = mocker.Mock(return_value=False)
    worker.progress_made = mocker.Mock()

    worker.run()

    worker.progress_made.emit.assert_called_once_with(1)
    mock_enrich.assert_called_once_with(mock_note, {"promptName": "test"})


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
    aqt.mw.col = mocker.Mock()
    aqt.mw.col.get_note.side_effect = Exception("note deleted")

    worker = MultipleNotesThreadWorker(notes=[999], browser=None, prompt_config={"promptName": "test"})
    worker.set_permission(True)
    worker.isInterruptionRequested = mocker.Mock(return_value=False)
    worker.progress_made = mocker.Mock()

    worker.run()

    worker.progress_made.emit.assert_called_once_with(1)


def test_worker_network_error_retry(mocker):
    import aqt
    mock_note = mocker.Mock(spec=Note)
    aqt.mw.col = mocker.Mock()
    aqt.mw.col.get_note.return_value = mock_note

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


def test_worker_non_network_error_skips_after_one_attempt(mocker):
    import aqt
    mock_note = mocker.Mock(spec=Note)
    aqt.mw.col = mocker.Mock()
    aqt.mw.col.get_note.return_value = mock_note

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
