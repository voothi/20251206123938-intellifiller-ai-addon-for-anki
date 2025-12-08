from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo

from .prompt_ui import Ui_Form
from .settings_window_ui import Ui_SettingsWindow
from .config_manager import ConfigManager
from .backup_manager import BackupManager
import json
import os

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
        self.backupNowBtn.clicked.connect(self.trigger_manual_backup)
        
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

        self.setup_password_fields()
        
        # Connect Backup Browse Buttons
        self.browseLocalPathBtn.clicked.connect(self.browse_local_path)
        self.browseExternalPathBtn.clicked.connect(self.browse_external_path)

    def setup_password_fields(self):
        """Configures API key fields to be masked with a toggle button."""
        fields = [
            self.apiKey, 
            self.anthropicKey, 
            self.geminiKey, 
            self.openrouterKey, 
            self.customKey, 
            self.encryptionKey,
            self.backupPassword
        ]
        
        addon_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_eye = QIcon(os.path.join(addon_dir, 'eye.svg'))
        self.icon_eye_off = QIcon(os.path.join(addon_dir, 'eye-off.svg'))

        for field in fields:
            self._add_eye_toggle(field)

    def _add_eye_toggle(self, line_edit):
        line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Action to toggle visibility
        action = line_edit.addAction(self.icon_eye, QLineEdit.ActionPosition.TrailingPosition)
        
        def toggle():
            if line_edit.echoMode() == QLineEdit.EchoMode.Password:
                line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
                action.setIcon(self.icon_eye_off)
            else:
                line_edit.setEchoMode(QLineEdit.EchoMode.Password)
                action.setIcon(self.icon_eye)
        
        action.triggered.connect(toggle)

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

        # Backup Settings
        backup = config.get("backup", {})
        self.backupEnabled.setChecked(backup.get("enabled", False))
        self.backupInterval.setValue(backup.get("intervalMinutes", 10))
        self.backupOnSettingsOpen.setChecked(backup.get("backupOnSettingsOpen", True))
        try:
            import pyzipper
            has_pyzipper = True
        except ImportError:
            has_pyzipper = False

        self.backupPassword.setText(backup.get("zipPassword", ""))
        if has_pyzipper:
            self.backupPassword.setPlaceholderText("Enter password for AES-256 encryption")
            self.backupPassword.setToolTip("Backups will be encrypted with strong AES-256.")
        else:
             self.backupPassword.setPlaceholderText("Encryption unavailable (missing pyzipper)")
             self.backupPassword.setToolTip("WARNING: 'pyzipper' module is missing. Password protection is disabled.\nRun scripts/setup_vendor.py to enable.")
        self.backupLocalPath.setText(backup.get("localPath", ""))
        self.backupExternalPath.setText(backup.get("externalPath", ""))
        
        self.keepTenMin.setValue(backup.get("keepTenMin", 6))
        self.keepHourly.setValue(backup.get("keepHourly", 24))
        self.keepDaily.setValue(backup.get("keepDaily", 30))
        self.keepMonthly.setValue(backup.get("keepMonthly", 12))
        self.keepYearly.setValue(backup.get("keepYearly", 5))


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
        
        # Add Backup Password to credentials (mapped)
        backup_pass = full_config.get('backup', {}).get('zipPassword', "")
        credentials["backupZipPassword"] = backup_pass
        
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
        
        # SECURITY STRIP: Remove password from backup settings before saving to plain text
        if 'backup' in settings and 'zipPassword' in settings['backup']:
            settings['backup']['zipPassword'] = ""
            
        ConfigManager.save_settings(settings)

        showInfo("Configuration saved.")
        self.config_saved = True
        self.original_config = json.dumps(full_config, sort_keys=True) # Update original config
        self.close()

    def get_current_config(self):
        # Start with existing settings to preserve hidden fields (like 'history')
        config = ConfigManager.load_settings()
        
        # Overlay UI values
        config["openaiModel"] = self.openaiModel.text()
        config["apiKey"] = self.apiKey.text()
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
        config["pipelines"] = self.pipelines
        
        # Backup Settings
        config["backup"] = {
            "enabled": self.backupEnabled.isChecked(),
            "intervalMinutes": self.backupInterval.value(),
            "backupOnSettingsOpen": self.backupOnSettingsOpen.isChecked(),
            "zipPassword": self.backupPassword.text(),
            "localPath": self.backupLocalPath.text(),
            "externalPath": self.backupExternalPath.text(),
            "keepTenMin": self.keepTenMin.value(),
            "keepHourly": self.keepHourly.value(),
            "keepDaily": self.keepDaily.value(),
            "keepMonthly": self.keepMonthly.value(),
            "keepYearly": self.keepYearly.value()
        }
        
        return config

    def browse_local_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Local Backup Directory", self.backupLocalPath.text())
        if directory:
            self.backupLocalPath.setText(directory)

    def browse_external_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select External Backup Directory", self.backupExternalPath.text())
        if directory:
            self.backupExternalPath.setText(directory)


    def trigger_manual_backup(self):
        # Save current settings to memory
        temp_config = self.get_current_config()
        # Persist to disk so BackupManager sees them
        ConfigManager.save_settings(temp_config)
        
        addon_dir = os.path.dirname(os.path.abspath(__file__))
        bm = BackupManager(ConfigManager, addon_dir)
        try:
            bm.perform_backup(force=True, backup_type='manual')
            showInfo("Backup completed successfully.\n\nCheck your configured local/external folders.")
        except Exception as e:
            showInfo(f"Backup failed: {str(e)}")

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
