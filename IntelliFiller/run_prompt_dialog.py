import re

from aqt.qt import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit, QComboBox, QCheckBox
from aqt import mw
from aqt.utils import showWarning


class RunPromptDialog(QDialog):
    def __init__(self, parentWindow, possible_fields, prompt_config):
        super().__init__(parentWindow)
        self.result = None
        self.possible_fields = possible_fields
        self.prompt_config = prompt_config
        self.setupLayout()

    def setupLayout(self):
        self.setWindowTitle(self.prompt_config["promptName"])
        layout = QVBoxLayout()

        self.prompt_editor = QTextEdit()
        self.prompt_editor.setPlainText(self.prompt_config["prompt"])

        self.target_field_editor = QComboBox()

        self.target_field_editor.addItems(self.possible_fields)
        if self.prompt_config["targetField"] in self.possible_fields:
            self.target_field_editor.setCurrentText(self.prompt_config["targetField"])

        self.label_target_field = QLabel("Target Field:")
        layout.addWidget(QLabel("Prompt:"))
        layout.addWidget(self.prompt_editor)
        layout.addWidget(self.label_target_field)
        layout.addWidget(self.target_field_editor)

        # Hide target field selection if response format is JSON
        if self.prompt_config.get("responseFormat") == "json":
            self.label_target_field.setVisible(False)
            self.target_field_editor.setVisible(False)

        # Add Save Changes Checkbox
        self.save_changes_checkbox = QCheckBox("Save changes to prompt configuration")
        layout.addWidget(self.save_changes_checkbox)

        run_button = QPushButton("Run")
        run_button.clicked.connect(self.try_to_accept)
        # Make it the default button and give it focus
        run_button.setAutoDefault(True)
        run_button.setDefault(True)

        layout.addWidget(run_button)
        self.setLayout(layout)
        run_button.setFocus()

    def try_to_accept(self):
        self.prompt_config["prompt"] = self.prompt_editor.toPlainText()
        self.prompt_config["targetField"] = self.target_field_editor.currentText()

        invalid_fields = get_invalid_fields_in_prompt(self.prompt_config["prompt"], self.possible_fields)
        if invalid_fields:
            showWarning("Some fields in your prompt do not exist in the notes: " + ", ".join(invalid_fields)
                        + "\nMake sure that you only use these fields " + ", ".join(self.possible_fields)
                        + "\nDouble-check the capital letters.")
            return
        
        # Include save flag in result
        self.result = {
            "config": self.prompt_config,
            "save": self.save_changes_checkbox.isChecked()
        }
        self.accept()

    def get_result(self):
        return self.result


def get_invalid_fields_in_prompt(prompt, valid_field_names):
    field_pattern = r'\{\{\{(.+?)\}\}\}'
    prompt_field_names = re.findall(field_pattern, prompt)
    pf_names_set = set(prompt_field_names)
    cf_names_set = set(valid_field_names)
    return pf_names_set.difference(cf_names_set)