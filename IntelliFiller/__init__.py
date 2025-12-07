from aqt import mw
from aqt.qt import *
from aqt.gui_hooks import editor_did_init_buttons
from aqt.editor import EditorMode, Editor
from aqt.browser import Browser
from aqt.addcards import AddCards
from anki.hooks import addHook
import os
import sys

# Ensure our addon’s vendor folder is the first thing in sys.path
vendor_path = os.path.join(os.path.dirname(__file__), 'vendor')
sys.path.insert(0, vendor_path)

# Debugging information
print("🔍 Anki Addon Loading Dependencies From:", vendor_path)
print("🔍 sys.path:", sys.path)


from .settings_editor import SettingsWindow
from .process_notes import process_notes, generate_for_single_note
from .run_prompt_dialog import RunPromptDialog

ADDON_NAME = 'IntelliFiller'



# Check if the correct typing_extensions is loaded
try:
    import typing_extensions
    print("✅ Loaded typing_extensions from:", typing_extensions.__file__)
except ImportError as e:
    print("❌ Failed to load typing_extensions:", e)

def handle_edit_current_mode(editor: Editor, prompt_config):
    editCurrentWindow: EditCurrent = editor.parentWindow
    common_fields = get_common_fields([editor.note.id])
    dialog = RunPromptDialog(editCurrentWindow, common_fields, prompt_config)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        result = dialog.get_result()
        updated_prompt_config = result["config"]
        if result["save"]:
            save_prompt_config(updated_prompt_config)
        generate_for_single_note(editor, updated_prompt_config)

def get_common_fields(selected_nodes_ids):
    common_fields = set(mw.col.getNote(selected_nodes_ids[0]).keys())
    for nid in selected_nodes_ids:
        note = mw.col.getNote(nid)
        note_fields = set(note.keys())
        common_fields = common_fields.intersection(note_fields)
    return list(common_fields)

def create_run_prompt_dialog_from_browser(browser, prompt_config):
    common_fields = get_common_fields(browser.selectedNotes())
    dialog = RunPromptDialog(browser, common_fields, prompt_config)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        result = dialog.get_result()
        updated_prompt_config = result["config"]
        if result["save"]:
            save_prompt_config(updated_prompt_config)
        process_notes(browser, updated_prompt_config)

def handle_browser_mode(editor: Editor, prompt_config):
    browser: Browser = editor.parentWindow
    common_fields = get_common_fields(browser.selectedNotes())
    dialog = RunPromptDialog(browser, common_fields, prompt_config)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        result = dialog.get_result()
        updated_prompt_config = result["config"]
        if result["save"]:
            save_prompt_config(updated_prompt_config)
        process_notes(browser, updated_prompt_config)

def handle_add_cards_mode(editor: Editor, prompt_config):
    addCardsWindow: AddCards = editor.parentWindow
    keys = editor.note.keys()
    dialog = RunPromptDialog(addCardsWindow, keys, prompt_config)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        result = dialog.get_result()
        updated_prompt_config = result["config"]
        if result["save"]:
            save_prompt_config(updated_prompt_config)
        generate_for_single_note(editor, updated_prompt_config)

def save_prompt_config(updated_prompt_config):
    config = mw.addonManager.getConfig(__name__)
    prompts = config.get("prompts", [])
    for i, p in enumerate(prompts):
        if p["promptName"] == updated_prompt_config["promptName"]:
            prompts[i] = updated_prompt_config
            break
    config["prompts"] = prompts
    mw.addonManager.writeConfig(__name__, config)

def create_run_prompt_dialog_from_editor(editor: Editor, prompt_config):
    if editor.editorMode == EditorMode.BROWSER:
        handle_browser_mode(editor, prompt_config)
    elif editor.editorMode == EditorMode.EDIT_CURRENT or editor.editorMode == EditorMode.ADD_CARDS:
        handle_edit_current_mode(editor, prompt_config)

def add_context_menu_items(browser, menu):
    submenu = QMenu(ADDON_NAME, menu)
    menu.addMenu(submenu)
    config = mw.addonManager.getConfig(__name__)
    prompts = config.get('prompts', [])
    max_favorites = config.get('maxFavorites', 3)
    history = config.get('history', [])

    # Smart Menu Logic
    # 1. Pinned prompts
    pinned_prompts = [p for p in prompts if p.get('pinned', False)]
    
    # 2. History prompts (excluding pinned ones to avoid duplicates)
    pinned_names = {p['promptName'] for p in pinned_prompts}
    history_prompts = []
    for name in history:
        # Find prompt config by name
        match = next((p for p in prompts if p['promptName'] == name), None)
        if match and match['promptName'] not in pinned_names:
            history_prompts.append(match)
            pinned_names.add(name) # Prevention of duplicates if history has dups
            
    # Combine and limit
    smart_prompts = (pinned_prompts + history_prompts)[:max_favorites]

    # Add Smart Items to top level menu
    if smart_prompts:
        for prompt_config in smart_prompts:
            action = QAction(prompt_config["promptName"], browser)
            # Use run_prompt_directly for smart menu items
            action.triggered.connect(lambda _, br=browser, pc=prompt_config: run_prompt_directly(br, pc))
            menu.addAction(action)
        
        menu.addSeparator()

    # Prompts Submenu
    prompts_menu = QMenu("Prompts", menu)
    menu.addMenu(prompts_menu)
    for prompt_config in prompts:
        action = QAction(prompt_config["promptName"], browser)
        action.triggered.connect(lambda _, br=browser, pc=prompt_config: create_run_prompt_dialog_from_browser(br, pc))
        prompts_menu.addAction(action)

    # Pipelines Submenu
    pipelines = config.get("pipelines", [])
    if pipelines:
        pipelines_menu = QMenu("Pipelines", menu)
        menu.addMenu(pipelines_menu)
        for pipeline in pipelines:
            action = QAction(pipeline["pipelineName"], browser)
            # Resolve prompts for pipeline
            resolved_prompts = []
            for prompt_name in pipeline["prompts"]:
                match = next((p for p in prompts if p['promptName'] == prompt_name), None)
                if match:
                    resolved_prompts.append(match)
            
            if resolved_prompts:
                action.triggered.connect(lambda _, br=browser, pl=resolved_prompts: process_notes(br, pl))
                pipelines_menu.addAction(action)


def run_prompt_directly(browser, prompt_config):
    """Directly run the prompt without showing the dialog."""
    process_notes(browser, prompt_config)


def open_settings():
    window = SettingsWindow(mw)
    window.exec()


def on_editor_button(editor):
    prompts = mw.addonManager.getConfig(__name__).get('prompts', [])

    menu = QMenu(editor.widget)
    for i, prompt in enumerate(prompts):
        action = QAction(f'Prompt {i + 1}: {prompt["promptName"]}', menu)
        action.triggered.connect(lambda _, p=prompt: create_run_prompt_dialog_from_editor(editor, p))
        menu.addAction(action)

    menu.exec(editor.widget.mapToGlobal(QPoint(0, 0)))


def on_setup_editor_buttons(buttons, editor):
    icon_path = os.path.join(os.path.dirname(__file__), "icon.svg")
    btn = editor.addButton(
        icon=icon_path,
        cmd="run_prompt",
        func=lambda e=editor: on_editor_button(e),
        tip=ADDON_NAME,
        keys=None,
        disables=False
    )
    buttons.append(btn)
    return buttons


addHook("browser.onContextMenu", add_context_menu_items)
mw.addonManager.setConfigAction(__name__, open_settings)
editor_did_init_buttons.append(on_setup_editor_buttons)
