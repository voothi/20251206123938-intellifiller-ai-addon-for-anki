from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtWidgets import QWidget, QDialog, QInputDialog, QMessageBox
from PyQt6.QtCore import QSize, Qt, QTimer
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo

from .prompt_ui import Ui_Form
from .settings_window_ui import Ui_SettingsWindow
from .config_manager import ConfigManager
import json

class PromptWidget(QWidget, Ui_Form):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        
        addon_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(addon_dir, 'remove.svg')
        self.removePromptButton.setIcon(QIcon(icon_path))
        self.removePromptButton.setIconSize(QSize(24, 24))


class SettingsWindow(QDialog, Ui_SettingsWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        
        self.setWindowTitle('ChatGPT Settings')
        config = ConfigManager.get_full_config()
        self.setup_config(config)
        self.saveButton.clicked.connect(self.saveConfig)
        self.addPromptButton.clicked.connect(self.add_new_prompt)
        
        # Connect API selection to stacked widget page
        self.selectedApi.currentIndexChanged.connect(self.stackedWidget.setCurrentIndex)
        # Set initial page based on config
        self.stackedWidget.setCurrentIndex(self.selectedApi.currentIndex())
        
        # Track initial state for unsaved changes detection
        self.config_saved = False
        # We need to capture the state *after* setup_config is called, but that uses the raw config object.
        # It's safer to call get_current_config() immediately after setup to establish baseline.
        # But wait, config object passed to setup_config IS the source of truth initially.
        self.original_config = json.dumps(config, sort_keys=True)

    def setWindowSize(self):
        screen_size = QGuiApplication.primaryScreen().geometry()
        self.resize(screen_size.width() * 0.8, screen_size.height() * 0.8)

    def setup_config(self, config):
        self.apiKey.setText(config.get("apiKey", ""))
        self.openaiModel.setText(config.get("openaiModel", ""))
        self.anthropicKey.setText(config.get("anthropicKey", ""))
        self.anthropicModel.setText(config.get("anthropicModel", ""))
        self.geminiKey.setText(config.get("geminiKey", ""))
        self.geminiModel.setText(config.get("geminiModel", ""))
        self.openrouterKey.setText(config.get("openrouterKey", ""))
        self.openrouterModel.setText(config.get("openrouterModel", ""))
        self.customUrl.setText(config.get("customUrl", ""))
        self.customKey.setText(config.get("customKey", ""))
        self.customModel.setText(config.get("customModel", ""))
        
        # Select correct API based on stored key (data)
        index = self.selectedApi.findData(config.get("selectedApi", "openai"))
        if index >= 0:
            self.selectedApi.setCurrentIndex(index)
        
        # Ensure correct stack page is shown after setting text
        self.stackedWidget.setCurrentIndex(self.selectedApi.currentIndex())
        
        self.emulate.setCurrentText(config.get("emulate", "no"))
        self.overwriteField.setChecked(config.get("overwriteField", False))
        self.flatMenu.setChecked(config.get("flatMenu", False))
        self.maxFavorites.setValue(config.get("maxFavorites", 3))
        # Default to True (Security by Default)
        self.obfuscateCreds.setChecked(config.get("obfuscateCreds", True))
        self.encryptionKey.setText(config.get("encryptionKey", ""))
        
        self.pipelinesList.currentRowChanged.connect(self.display_pipeline_details)
        self.addPipelineButton.clicked.connect(self.add_new_pipeline)
        self.removePipelineButton.clicked.connect(self.remove_selected_pipeline)
        self.pipelineName.textChanged.connect(self.update_current_pipeline_name)
        self.pipelinePinnedCheckbox.clicked.connect(self.update_current_pipeline_pinned)
        self.addPromptToPipelineButton.clicked.connect(self.add_prompt_to_pipeline)
        self.removePromptFromPipelineButton.clicked.connect(self.remove_prompt_from_pipeline)

        self.pipelines = config.get("pipelines", [])
        self.refresh_pipelines_list()

        self.promptWidgets = []
        for prompt in config.get("prompts", []):
            self.add_prompt(prompt)

    def refresh_pipelines_list(self):
        self.pipelinesList.clear()
        for pipeline in self.pipelines:
            self.pipelinesList.addItem(pipeline["pipelineName"])

    def display_pipeline_details(self, row):
        if row < 0 or row >= len(self.pipelines):
            self.pipelineDetailsGroup.setEnabled(False)
            self.pipelineName.clear()
            self.pipelinePinnedCheckbox.setChecked(False)
            self.pipelinePromptsList.clear()
            return

        self.pipelineDetailsGroup.setEnabled(True)
        pipeline = self.pipelines[row]
        self.pipelineName.setText(pipeline["pipelineName"])
        self.pipelinePinnedCheckbox.setChecked(pipeline.get("pinned", False))
        
        self.pipelinePromptsList.clear()
        for prompt_name in pipeline["prompts"]:
            self.pipelinePromptsList.addItem(prompt_name)

    def add_new_pipeline(self):
        new_pipeline = {"pipelineName": "New Pipeline", "prompts": [], "pinned": False}
        self.pipelines.append(new_pipeline)
        self.refresh_pipelines_list()
        self.pipelinesList.setCurrentRow(len(self.pipelines) - 1)

    def remove_selected_pipeline(self):
        row = self.pipelinesList.currentRow()
        if row >= 0:
            del self.pipelines[row]
            self.refresh_pipelines_list()

    def update_current_pipeline_name(self, text):
        row = self.pipelinesList.currentRow()
        if row >= 0:
            self.pipelines[row]["pipelineName"] = text
            item = self.pipelinesList.item(row)
            item.setText(text)

    def update_current_pipeline_pinned(self):
        row = self.pipelinesList.currentRow()
        if row >= 0:
            self.pipelines[row]["pinned"] = self.pipelinePinnedCheckbox.isChecked()

    def add_prompt_to_pipeline(self):
        row = self.pipelinesList.currentRow()
        if row < 0:
            return

        # Get list of all available prompts
        available_prompts = [p.promptNameInput.text() for p in self.promptWidgets]
        if not available_prompts:
            showInfo("No prompts available to add.")
            return

        prompt_name, ok = QInputDialog.getItem(
            self, "Select Prompt", "Choose a prompt to add:", available_prompts, 0, False
        )
        if ok and prompt_name:
            self.pipelines[row]["prompts"].append(prompt_name)
            self.pipelinePromptsList.addItem(prompt_name)

    def remove_prompt_from_pipeline(self):
        pipeline_row = self.pipelinesList.currentRow()
        prompt_row = self.pipelinePromptsList.currentRow()
        if pipeline_row >= 0 and prompt_row >= 0:
            del self.pipelines[pipeline_row]["prompts"][prompt_row]
            self.pipelinePromptsList.takeItem(prompt_row)


    def add_new_prompt(self):
        promptWidget = self.add_prompt({
            "prompt": "",
            "targetField": "",
            "promptName": ""
        })
        
        # Scroll to ensure the new widget is fully visible
        # Use ensureWidgetVisible which handles scrolling logic better than setting value to maximum
        # Increase delay to 50ms to ensure layout has fully recalculated size
        QTimer.singleShot(50, lambda: self.scrollArea.ensureWidgetVisible(promptWidget))
        
        # Set focus to the prompt name
        promptWidget.promptNameInput.setFocus()

    def add_prompt(self, prompt):
        promptWidget = PromptWidget()
        promptWidget.promptInput.setPlainText(prompt["prompt"])
        promptWidget.targetFieldInput.setText(prompt["targetField"])
        promptWidget.promptNameInput.setText(prompt["promptName"])
        promptWidget.pinnedCheckbox.setChecked(prompt.get("pinned", False))
        
        # JSON / Multi-field setup
        fmt = prompt.get("responseFormat", "text")
        promptWidget.responseFormat.setCurrentText("JSON" if fmt == "json" else "Text")
        
        mapping = prompt.get("fieldMapping", {})
        mapping_text = ""
        for k, v in mapping.items():
            mapping_text += f"{k}: {v}\n"
        promptWidget.fieldMappingInput.setPlainText(mapping_text.strip())
        
        # Connect visibility toggle
        promptWidget.responseFormat.currentTextChanged.connect(
            lambda text, w=promptWidget: self.toggle_prompt_format(w, text))
        
        # Initial state
        self.toggle_prompt_format(promptWidget, promptWidget.responseFormat.currentText())

        promptWidget.removePromptButton.clicked.connect(
            lambda: self.remove_prompt(promptWidget))
        
        self.promptsLayout.addWidget(promptWidget)
        self.promptWidgets.append(promptWidget)
        return promptWidget

    def toggle_prompt_format(self, widget, text):
        is_json = (text == "JSON")
        widget.targetFieldInput.setVisible(not is_json)
        widget.fieldMappingInput.setVisible(is_json)
        # Updates placeholder based on mode
        if is_json:
             widget.targetFieldInput.clear() # Clear it? Or keep it? Maybe keep it.

    def remove_prompt(self, promptWidgetToRemove):
        self.promptWidgets.remove(promptWidgetToRemove)
        self.promptsLayout.removeWidget(promptWidgetToRemove)
        promptWidgetToRemove.deleteLater()

    def saveConfig(self):
        full_config = self.get_current_config()
        
        # 1. Credentials
        cred_keys = [
            "apiKey", "openaiModel", 
            "anthropicKey", "anthropicModel", 
            "geminiKey", "geminiModel", 
            "openrouterKey", "openrouterModel", 
            "customUrl", "customKey", "customModel"
        ]
        credentials = {k: full_config.get(k, "") for k in cred_keys}
        
        # Pull obfuscation setting directly from UI since it's part of 'settings', not 'credentials'
        should_obfuscate = self.obfuscateCreds.isChecked()
        custom_key = self.encryptionKey.text()
        
        # Save credentials using the NEW key (re-encryption happens here automatically)
        ConfigManager.save_credentials(credentials, key=custom_key, obfuscate=should_obfuscate)

        # 2. Prompts
        # Capture state BEFORE saving to know what to delete later
        existing_prompts = ConfigManager.list_prompts()
        existing_names = set(p['promptName'] for p in existing_prompts)
        new_names = set(p['promptName'] for p in full_config['prompts'])
        
        # Save all current prompts FIRST (Safety Fix)
        for prompt in full_config['prompts']:
            ConfigManager.save_prompt(prompt)

        # Remove obsolete files (Safe to do now)
        for name in existing_names:
            if name not in new_names:
                ConfigManager.delete_prompt_file(name)

        # 3. Settings (exclude credentials and prompts)
        settings = {}
        for k, v in full_config.items():
            if k not in cred_keys and k != "prompts":
                settings[k] = v
        
        ConfigManager.save_settings(settings)

        showInfo("Configuration saved.")
        self.config_saved = True
        self.original_config = json.dumps(full_config, sort_keys=True) # Update original config
        self.close()

    def get_current_config(self):
        # We need to load settings first to get the key, then load credentials
        # But here we want the FULL config to populate UI.
        
        # 1. Load Settings
        settings = ConfigManager.load_settings()
        encryption_key = settings.get("encryptionKey", "")
        
        # 2. Load Credentials using that key
        credentials = ConfigManager.load_credentials(key=encryption_key)
        
        # 3. Load Prompts
        prompts = ConfigManager.list_prompts()
        
        # Merge
        full_config = {**settings, **credentials}
        full_config["prompts"] = prompts
        return full_config
        config["openaiModel"] = self.openaiModel.text()
        config["anthropicKey"] = self.anthropicKey.text()
        config["anthropicModel"] = self.anthropicModel.text()
        config["geminiKey"] = self.geminiKey.text()
        config["geminiModel"] = self.geminiModel.text()
        config["openrouterKey"] = self.openrouterKey.text()
        config["openrouterModel"] = self.openrouterModel.text()
        config["customUrl"] = self.customUrl.text()
        config["customKey"] = self.customKey.text()
        config["customModel"] = self.customModel.text()
        config["selectedApi"] = self.selectedApi.currentData()
        config["emulate"] = self.emulate.currentText()
        config["overwriteField"] = self.overwriteField.isChecked()
        config["flatMenu"] = self.flatMenu.isChecked()
        config["maxFavorites"] = self.maxFavorites.value()
        config["obfuscateCreds"] = self.obfuscateCreds.isChecked()
        config["encryptionKey"] = self.encryptionKey.text()
        
        config["prompts"] = []
        for promptWidget in self.promptWidgets:
            promptInput = promptWidget.promptInput
            targetFieldInput = promptWidget.targetFieldInput
            promptNameInput = promptWidget.promptNameInput
            
            # Helper to parse mapping
            fmt_text = promptWidget.responseFormat.currentText()
            fmt = "json" if fmt_text == "JSON" else "text"
            
            mapping = {}
            if fmt == "json":
                lines = promptWidget.fieldMappingInput.toPlainText().split('\n')
                for line in lines:
                    if ':' in line:
                        k, v = line.split(':', 1)
                        mapping[k.strip()] = v.strip()
            
            config["prompts"].append({
                "prompt": promptInput.toPlainText(),
                "targetField": targetFieldInput.text(),
                "promptName": promptNameInput.text(),
                "pinned": promptWidget.pinnedCheckbox.isChecked(),
                "responseFormat": fmt,
                "fieldMapping": mapping
            })
        
        config["pipelines"] = self.pipelines
        return config

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_S and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.saveConfig()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.config_saved:
            event.accept()
            return

        current_config = self.get_current_config()
        current_config_str = json.dumps(current_config, sort_keys=True)
        
        if current_config_str != self.original_config:
            reply = QMessageBox.question(
                self, 
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them before closing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                self.saveConfig()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
