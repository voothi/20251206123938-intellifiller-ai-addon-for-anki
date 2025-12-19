from aqt.qt import QThread, pyqtSignal, QDialog, QVBoxLayout, QHBoxLayout, QProgressBar, QPushButton, QLabel, QLineEdit, Qt, QAction, QStyle, QApplication
from aqt import mw
from aqt.utils import showWarning

from .data_request import create_prompt, send_prompt_to_llm
from .modify_notes import fill_field_for_note_in_editor, fill_field_for_note_not_in_editor
from .config_manager import ConfigManager
from .execution_manager import ExecutionManager
from anki.notes import Note, NoteId
import sys
import time
import random

def get_deck_name(note):
    try:
        if note.cards():
            did = note.cards()[0].did
            deck = mw.col.decks.get(did)
            if deck:
                return deck['name']
    except:
        pass
    return "Unknown Deck"

class MultipleNotesThreadWorker(QThread):
    progress_made = pyqtSignal(int)
    status_update = pyqtSignal(str)
    deck_update = pyqtSignal(str)
    refresh_browser = pyqtSignal()
    # error_occurred = pyqtSignal(str) # No longer needed for UI, we use stderr directly

    def __init__(self, notes, browser, prompt_config):
        super().__init__()
        self.notes = notes
        self.browser = browser
        self.prompt_config = prompt_config
        self.has_shown_error = False
        
        # Load Batch Settings
        settings = ConfigManager.load_settings()
        batch_cfg = settings.get("batchProcessing", {})
        self.batch_enabled = batch_cfg.get("enabled", True)
        self.batch_size = batch_cfg.get("batchSize", 20)
        self.batch_delay = batch_cfg.get("batchDelay", 5)
        self.random_delay = batch_cfg.get("randomDelay", True)
        self.random_min = batch_cfg.get("randomDelayMin", 0)
        self.random_max = batch_cfg.get("randomDelayMax", 10)
        
        self.run_permission = False
        self.is_user_paused = False

    def set_permission(self, allowed: bool):
        self.run_permission = allowed

    def set_user_paused(self, paused: bool):
        self.is_user_paused = paused

    def run(self):
        total_notes = len(self.notes)
        
        for i, item in enumerate(self.notes):
            # Check for pause before starting next item
            # Check state before processing
            while not self.run_permission:
                if self.isInterruptionRequested():
                    return
                
                if self.is_user_paused:
                    self.status_update.emit("Paused by user. Click Resume to continue.")
                else:
                    self.status_update.emit("Waiting in queue...")
                
                time.sleep(0.1)
                
            if i > 0 and self.is_user_paused == False: # Only say resuming if we were actually ensuring progress
                 # If we just came out of a wait, update status? 
                 # Actually the loop above handles the wait. 
                 pass

            # Batch Processing Delay
            # Check if enabled, if we hit the batch limit, and if it's NOT the last item
            if self.batch_enabled and i > 0 and (i % self.batch_size == 0):
                # We are about to process usage number 'i+1'. i is 0-indexed. 
                # e.g. batch=5. i=0,1,2,3,4 (5 items done). Loop i=5 triggers check?
                # Actually, standard is check after N items. 
                # i starts at 0. processing item i. 
                # We want to pause BEFORE item i if i is a multiple of batch_size.
                
                # Signal the UI to refresh the browser list so user sees progress
                self.refresh_browser.emit()
                
                remaining = self.batch_delay
                
                if self.random_delay:
                    extra = random.randint(self.random_min, self.random_max)
                    self.status_update.emit(f"Adding random delay variance: +{extra}s")
                    remaining += extra
                
                while remaining > 0:
                    if self.isInterruptionRequested():
                        return # Exit run immediately
                    
                    self.status_update.emit(f"Paused for batch limit... continuing in {remaining}s")
                    time.sleep(1)
                    remaining -= 1
                
                # Restore status text
                self.status_update.emit(f"Resuming processing...")

            # Retry loop for the distinct note
            while True:
                if self.isInterruptionRequested():
                    break
                
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
                        break # Break retry loop, effectively skipping this note
                    
                    # Update Deck Name info
                    deck_name = get_deck_name(note)
                    self.deck_update.emit(deck_name)

                    # prompt_config can be a dict (single prompt) or list (pipeline)
                    if isinstance(self.prompt_config, list):
                        for p_config in self.prompt_config:
                            enrich_without_editor(note, p_config)
                    else:
                        enrich_without_editor(note, self.prompt_config)
                    
                    # If we reached here, success!
                    break 

                except Exception as e:
                    err_str = str(e).lower()
                    # Check for common network/timeout keywords
                    is_net_error = any(x in err_str for x in ["connect", "time", "network", "socket", "proxy", "50", "429"])
                    
                    # Logic: Immediate feedback, "Original Window", One time only.
                    if not self.has_shown_error:
                        sys.stderr.write(f"IntelliFiller Error: {str(e)}")
                        self.has_shown_error = True
                    
                    if is_net_error:
                        # If filter matches network error, wait and retry
                        # Check cancel again before sleeping
                        if self.isInterruptionRequested():
                            break
                        time.sleep(3)
                        continue
                    else:
                        # Logic/Template error -> Skip note
                        pass
                    
                    # Store internally if needed, but we aren't showing a summary anymore
                    break

            # If external loop was broken due to cancel
            if self.isInterruptionRequested():
                break

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
        
        self.deck_line_edit = QLineEdit()
        self.deck_line_edit.setReadOnly(True)
        self.deck_line_edit.setPlaceholderText("Deck path...")
        self.deck_line_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # Ensure it doesn't change window size, just fills available width
        self.deck_line_edit.setStyleSheet("color: white; background: transparent; border: none;") # Optional styling to make it look cleaner if desired, or keep standard look.
        # User asked for "separate field", so standard border might be better to indicate copyability. 
        # But also "standard window should be size it was before". 
        # A standard QLineEdit definitely looks like a field.
        self.deck_line_edit.setStyleSheet("") # Reset to default style to look like a field
        
        # Add Copy Action inside the field
        copy_icon = self.style().standardIcon(QStyle.SP_FileIcon) # Generic file icon as placeholder for Copy
        copy_action = self.deck_line_edit.addAction(copy_icon, QLineEdit.TrailingPosition)
        copy_action.setToolTip("Copy Deck Path")
        copy_action.triggered.connect(self.copy_deck_path)
        
        layout.addWidget(self.deck_line_edit)

        # Button Layout
        button_layout = QHBoxLayout()

        self.pause_button = QPushButton('Pause')
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setAutoDefault(False)
        button_layout.addWidget(self.pause_button)
        
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.cancel)
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.setDefault(False)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setWindowTitle("Processing Notes...")
        self.resize(350, 100)

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.counter_label.setText(f"{value} of {self.progress_bar.maximum()} processed")

    def run_task(self, notes, prompt_config):
        self.progress_bar.setMaximum(len(notes))
        self.progress_bar.setValue(0)
        self.errors = []
        self.worker = MultipleNotesThreadWorker(notes, mw.col, prompt_config)  # pass the notes and prompt_config
        self.worker.progress_made.connect(self.update_progress)
        self.worker.status_update.connect(self.update_status)
        self.worker.deck_update.connect(self.update_deck_info)
        self.worker.refresh_browser.connect(self.on_refresh_browser)
        self.worker.finished.connect(self.on_worker_finished)  # connect the finish signal to a slot
        
        # Instead of starting immediately, add to global queue
        self.update_status("Waiting in queue...")
        self.show()
        ExecutionManager.instance().enqueue(self)

    def start_processing(self):
        """Called by ExecutionManager when it's our turn"""
        if self.worker:
            self.worker.set_permission(True)
            if not self.worker.isRunning():
                self.worker.start()
        self.cancel_button.clearFocus()
        self.pause_button.setFocus()

    def toggle_pause(self):
        if not self.worker:
            return
            
        # Check if we are asking to Pause or Resume based on current State
        # If user_paused is True, we are Resuming
        if self.worker.is_user_paused:
            # RESUME ACTION
            self.worker.set_user_paused(False)
            self.pause_button.setText("Pause")
            
            # CRITICAL: We do NOT give permission immediately.
            # We enqueue ourselves. Queue will give permission when free.
            ExecutionManager.instance().enqueue(self)
        else:
            # PAUSE ACTION
            self.worker.set_user_paused(True)
            self.worker.set_permission(False) # Stop running
            self.pause_button.setText("Resume")
            
            # Yield execution to others
            ExecutionManager.instance().yield_execution(self)

    def on_refresh_browser(self):
        mw.reset()

    def copy_deck_path(self):
        text = self.deck_line_edit.text()
        if text:
            QApplication.clipboard().setText(text)
            self.deck_line_edit.setSelection(0, len(text)) # Visual feedback: select all

    def update_status(self, text):
        self.counter_label.setText(text)

    def update_deck_info(self, deck_name):
        text = f"deck:{deck_name}"
        self.deck_line_edit.setText(text)
        # Scroll to end to show the final part of the path
        self.deck_line_edit.setCursorPosition(len(text))
        # self.setWindowTitle(f"Processing {deck_name}...") # User requested to stop changing title

    def on_worker_finished(self):
        self.update_progress(
            self.progress_bar.maximum())  # when the worker is finished, set the progress bar to maximum
        
        # If we are in browser, reset
        # If we are in editor single mode?
        # mw.reset() is good for browser.
        # For AddCards/EditCurrent, we might need to trigger a reload of the note in the editor?
        mw.reset() 
        ExecutionManager.instance().notify_finished(self)
        self.close()  # close the dialog when the worker finishes

    def cancel(self):
        if self.worker:
            self.worker.requestInterruption()
            self.worker.wait(100) # Optional: give it a tiny moment to check flag
        
        # Reset UI (e.g. Browser list) so partially processed changes are visible
        mw.reset()
        
        # Close immediately so the user isn't stuck
        # Close immediately so the user isn't stuck
        ExecutionManager.instance().notify_finished(self)
        self.close()

    def reject(self):
        # Override reject (Esc/CloseButton) to trigger cancellation cleanup
        self.cancel()
        super().reject()


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