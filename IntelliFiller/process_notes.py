from aqt.qt import QThread, pyqtSignal, QDialog, QVBoxLayout, QProgressBar, QPushButton, QLabel
from aqt import mw
from aqt.utils import showWarning

from .data_request import create_prompt, send_prompt_to_llm
from .modify_notes import fill_field_for_note_in_editor, fill_field_for_note_not_in_editor
from .config_manager import ConfigManager
from anki.notes import Note, NoteId
import sys

class MultipleNotesThreadWorker(QThread):
    progress_made = pyqtSignal(int)
    # error_occurred = pyqtSignal(str) # No longer needed for UI, we use stderr directly

    def __init__(self, notes, browser, prompt_config):
        super().__init__()
        self.notes = notes
        self.browser = browser
        self.prompt_config = prompt_config
        self.has_shown_error = False

    def run(self):
        for i, item in enumerate(self.notes):
            if self.isInterruptionRequested():
                break
            else:
                # Fetch note once per note-processing loop to ensure pipeline steps share the same object
                # and see each other's updates immediately (before flush/reload).
                try:
                    try:
                        if isinstance(item, Note):
                            note = item
                        else:
                            # Assume it's a NoteId (int)
                            note = mw.col.get_note(item)
                    except Exception:
                        # If note deleted or not found, skip
                        self.progress_made.emit(i + 1)
                        continue

                    # prompt_config can be a dict (single prompt) or list (pipeline)
                    if isinstance(self.prompt_config, list):
                        for p_config in self.prompt_config:
                            enrich_without_editor(note, p_config)
                    else:
                        enrich_without_editor(note, self.prompt_config)
                except Exception as e:
                    # Logic: Immediate feedback, "Original Window", One time only.
                    if not self.has_shown_error:
                        sys.stderr.write(f"IntelliFiller Error: {str(e)}")
                        self.has_shown_error = True
                    
                    # Store internally if needed, but we aren't showing a summary anymore
                    pass

            self.progress_made.emit(i + 1)


class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super(ProgressDialog, self).__init__(parent)
        self.worker = None
        self.errors = []
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
        self.errors = []
        self.worker = MultipleNotesThreadWorker(notes, mw.col, prompt_config)  # pass the notes and prompt_config
        self.worker.progress_made.connect(self.update_progress)
        self.worker.finished.connect(self.on_worker_finished)  # connect the finish signal to a slot
        self.worker.start()
        self.show()

    def on_worker_finished(self):
        self.update_progress(
            self.progress_bar.maximum())  # when the worker is finished, set the progress bar to maximum
        
        # If we are in browser, reset
        # If we are in editor single mode?
        # mw.reset() is good for browser.
        # For AddCards/EditCurrent, we might need to trigger a reload of the note in the editor?
        mw.reset() 
        self.close()  # close the dialog when the worker finishes

    def cancel(self):
        if self.worker:
            self.worker.requestInterruption()
            self.worker.wait(100) # Optional: give it a tiny moment to check flag
        
        # Close immediately so the user isn't stuck
        self.close()


import json
import re

def parse_llm_json(response_text):
    """
    Parses JSON from LLM response, handling markdown code blocks.
    Returns dict or None if parsing fails.
    """
    if not response_text:
        return None
        
    # Remove markdown code blocks
    # Pattern to match ```json ... ``` or just ``` ... ```
    pattern = r"```(?:json)?\s*(.*?)\s*```"
    match = re.search(pattern, response_text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        json_str = response_text
        
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Fallback: try to find start/end braces if there's extra text
        start = json_str.find('{')
        end = json_str.rfind('}')
        if start != -1 and end != -1:
             try:
                 return json.loads(json_str[start:end+1])
             except:
                 pass
        return None

def apply_response_to_note(note_or_editor, prompt_config, response, is_editor=False):
    """
    Applies the LLM response to the note (or editor) based on format.
    """
    fmt = prompt_config.get("responseFormat", "text")
    overwrite = prompt_config.get('overwriteField', False)
    
    if fmt == "json":
        data = parse_llm_json(response)
        if not data:
            # We raise here so the worker catches it
            raise ValueError(f"Failed to parse JSON response for prompt '{prompt_config.get('promptName', '?')}'")

        mapping = prompt_config.get("fieldMapping", {})
        for json_key, target_field in mapping.items():
            if json_key in data:
                val = data[json_key]
                # Convert non-string values to string
                if isinstance(val, (dict, list)):
                    val = json.dumps(val, ensure_ascii=False)
                val = str(val)
                
                if is_editor:
                    fill_field_for_note_in_editor(val, target_field, note_or_editor, overwrite)
                else:
                    fill_field_for_note_not_in_editor(val, note_or_editor, target_field, overwrite)
            else:
                # Key missing in response? Warning logic could go here.
                pass
                
    else:
        # Text mode (legacy)
        target_field = prompt_config['targetField']
        if is_editor:
            fill_field_for_note_in_editor(response, target_field, note_or_editor, overwrite)
        else:
            fill_field_for_note_not_in_editor(response, note_or_editor, target_field, overwrite)


def enrich_without_editor(nid_or_note, prompt_config):
    """generate"""
    if isinstance(nid_or_note, Note):
        note = nid_or_note
    else:
        note = mw.col.get_note(nid_or_note)
        
    prompt = create_prompt(note, prompt_config)
    response = send_prompt_to_llm(prompt)
    
    # Delegate application logic
    apply_response_to_note(note, prompt_config, response, is_editor=False)


def process_notes(browser, prompt_config, pipeline_name=None):
    selected_notes = browser.selectedNotes()
    if not selected_notes:
        showWarning("No notes selected.")
        return

    def on_save_completed():
        # Inject global overwrite setting into prompt_config(s)
        settings = ConfigManager.load_settings()
        overwrite_global = settings.get('overwriteField', False)
        
        if isinstance(prompt_config, list):
            for p in prompt_config:
                p['overwriteField'] = overwrite_global
        else:
            prompt_config['overwriteField'] = overwrite_global

        # Update history
        # If it's a pipeline, use pipeline_name. If single prompt, use promptName.
        item_name = pipeline_name if pipeline_name else (prompt_config['promptName'] if not isinstance(prompt_config, list) else None)
        
        if item_name:
            update_history_config(item_name)

        # Use Threaded Worker for ALL cases to prevent UI freezing
        progress_dialog = ProgressDialog(browser)
        progress_dialog.run_task(selected_notes, prompt_config)

    # If the editor is active and contains changes, save them first!
    if browser.editor:
        browser.editor.saveNow(on_save_completed)
    else:
        on_save_completed()


def process_single_note(editor, prompt_config):
    """
    Process a single note from an editor context (EditCurrent, AddCards, etc.).
    Reuses proper threading to prevent UI blocking.
    """
    if not editor or not editor.note:
        return

    def on_save_completed():
        target_note = editor.note
        
        # We need a parent for the dialog. Use the window containing the editor.
        parent_window = editor.parentWindow
        
        progress_dialog = ProgressDialog(parent_window)
        # We pass a list containing the Note object itself to avoid DB fetch issues for AddCards
        progress_dialog.run_task([target_note], prompt_config)

    # 1. Save changes in editor to note
    editor.saveNow(on_save_completed)


def update_history_config(item_name):
    settings = ConfigManager.load_settings()
    history = settings.get('history', [])
    # max_img = 10 
    
    # Move to front if exists, else add to front
    if item_name in history:
        history.remove(item_name)
    history.insert(0, item_name)
    
    # Limit size (arbitrary limit to keep config clean, e.g. 20)
    history = history[:20]
    
    settings['history'] = history
    ConfigManager.save_settings(settings)