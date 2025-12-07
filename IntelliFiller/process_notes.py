from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QPushButton, QLabel
from aqt import mw
from aqt.utils import showWarning

from .data_request import create_prompt, send_prompt_to_llm
from .modify_notes import fill_field_for_note_in_editor, fill_field_for_note_not_in_editor
from anki.notes import Note, NoteId


class MultipleNotesThreadWorker(QThread):
    progress_made = pyqtSignal(int)

    def __init__(self, notes, browser, prompt_config):
        super().__init__()
        self.notes = notes
        self.browser = browser
        self.prompt_config = prompt_config

    def run(self):
        for i, nid in enumerate(self.notes):
            if self.isInterruptionRequested():
                break
            else:
                enrich_without_editor(nid, self.prompt_config)
            self.progress_made.emit(i + 1)


class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super(ProgressDialog, self).__init__(parent)
        self.worker = None
        layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.counter_label = QLabel()
        layout.addWidget(self.counter_label)

        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.cancel)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)
        self.setWindowTitle("Processing Notes...")

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.counter_label.setText(f"{value} of {self.progress_bar.maximum()} processed")

    def run_task(self, notes, prompt_config):
        self.progress_bar.setMaximum(len(notes))
        self.progress_bar.setValue(0)
        self.worker = MultipleNotesThreadWorker(notes, mw.col, prompt_config)  # pass the notes and prompt_config
        self.worker.progress_made.connect(self.update_progress)
        self.worker.finished.connect(self.on_worker_finished)  # connect the finish signal to a slot
        self.worker.start()
        self.show()

    def on_worker_finished(self):
        self.update_progress(
            self.progress_bar.maximum())  # when the worker is finished, set the progress bar to maximum
        mw.reset() # Refresh Anki UI (including browser)
        self.close()  # close the dialog when the worker finishes

    def cancel(self):
        if self.worker:
            self.worker.requestInterruption()
        self.close()


def generate_for_single_note(editor, prompt_config):
    """Generate text for a single note (editor note)."""
    prompt = create_prompt(editor.note, prompt_config)
    response = send_prompt_to_llm(prompt)

    target_field = prompt_config['targetField']
    overwrite = prompt_config.get('overwriteField', False)
    fill_field_for_note_in_editor(response, target_field, editor, overwrite)


def enrich_without_editor(nid: NoteId, prompt_config):
    """generate"""
    note = mw.col.get_note(nid)
    prompt = create_prompt(note, prompt_config)
    response = send_prompt_to_llm(prompt)
    overwrite = prompt_config.get('overwriteField', False)
    fill_field_for_note_not_in_editor(response, note, prompt_config['targetField'], overwrite)


def process_notes(browser, prompt_config):
    selected_notes = browser.selectedNotes()
    if not selected_notes:
        showWarning("No notes selected.")
        return

    # Inject global overwrite setting into prompt_config
    config = mw.addonManager.getConfig(__name__)
    prompt_config['overwriteField'] = config.get('overwriteField', False)

    # Update history
    update_history_config(prompt_config['promptName'])

    if len(selected_notes) == 1 and browser.editor and browser.editor.note:
        generate_for_single_note(browser.editor, prompt_config)
    else:
        progress_dialog = ProgressDialog(browser)
        progress_dialog.run_task(selected_notes, prompt_config)

def update_history_config(prompt_name):
    config = mw.addonManager.getConfig(__name__)
    history = config.get('history', [])
    max_img = 10 # Keep more history than visible maxFavorites to allow flexibility, or just enough
    
    # Move to front if exists, else add to front
    if prompt_name in history:
        history.remove(prompt_name)
    history.insert(0, prompt_name)
    
    # Limit size (arbitrary limit to keep config clean, e.g. 20)
    history = history[:20]
    
    config['history'] = history
    mw.addonManager.writeConfig(__name__, config)