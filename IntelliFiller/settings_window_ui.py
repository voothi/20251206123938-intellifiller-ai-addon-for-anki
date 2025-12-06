# -*- coding: utf-8 -*-

from PyQt6 import QtCore, QtGui, QtWidgets

class Ui_SettingsWindow(object):
    def setupUi(self, SettingsWindow):
        SettingsWindow.setObjectName("SettingsWindow")
        SettingsWindow.setWindowModality(QtCore.Qt.WindowModality.NonModal)
        SettingsWindow.resize(805, 800)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, 
                                         QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(SettingsWindow.sizePolicy().hasHeightForWidth())
        SettingsWindow.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(SettingsWindow)
        self.verticalLayout.setObjectName("verticalLayout")

        # OpenAI API Key
        self.labelApiKey = QtWidgets.QLabel(SettingsWindow)
        self.labelApiKey.setObjectName("labelApiKey")
        self.verticalLayout.addWidget(self.labelApiKey)
        self.apiKey = QtWidgets.QLineEdit(SettingsWindow)
        self.apiKey.setObjectName("apiKey")
        self.verticalLayout.addWidget(self.apiKey)

        # OpenAI Model
        self.labelOpenaiModel = QtWidgets.QLabel(SettingsWindow)
        self.labelOpenaiModel.setObjectName("labelOpenaiModel")
        self.verticalLayout.addWidget(self.labelOpenaiModel)
        self.openaiModel = QtWidgets.QLineEdit(SettingsWindow)
        self.openaiModel.setObjectName("openaiModel")
        self.verticalLayout.addWidget(self.openaiModel)

        # Anthropic API Key
        self.labelAnthropicKey = QtWidgets.QLabel(SettingsWindow)
        self.labelAnthropicKey.setObjectName("labelAnthropicKey")
        self.verticalLayout.addWidget(self.labelAnthropicKey)
        self.anthropicKey = QtWidgets.QLineEdit(SettingsWindow)
        self.anthropicKey.setObjectName("anthropicKey")
        self.verticalLayout.addWidget(self.anthropicKey)

        # Anthropic Model
        self.labelAnthropicModel = QtWidgets.QLabel(SettingsWindow)
        self.labelAnthropicModel.setObjectName("labelAnthropicModel")
        self.verticalLayout.addWidget(self.labelAnthropicModel)
        self.anthropicModel = QtWidgets.QLineEdit(SettingsWindow)
        self.anthropicModel.setObjectName("anthropicModel")
        self.verticalLayout.addWidget(self.anthropicModel)

        # Gemini API Key
        self.labelGeminiKey = QtWidgets.QLabel(SettingsWindow)
        self.labelGeminiKey.setObjectName("labelGeminiKey")
        self.verticalLayout.addWidget(self.labelGeminiKey)
        self.geminiKey = QtWidgets.QLineEdit(SettingsWindow)
        self.geminiKey.setObjectName("geminiKey")
        self.verticalLayout.addWidget(self.geminiKey)

        # Gemini Model
        self.labelGeminiModel = QtWidgets.QLabel(SettingsWindow)
        self.labelGeminiModel.setObjectName("labelGeminiModel")
        self.verticalLayout.addWidget(self.labelGeminiModel)
        self.geminiModel = QtWidgets.QLineEdit(SettingsWindow)
        self.geminiModel.setObjectName("geminiModel")
        self.verticalLayout.addWidget(self.geminiModel)

        # API Selection
        self.labelSelectedApi = QtWidgets.QLabel(SettingsWindow)
        self.labelSelectedApi.setObjectName("labelSelectedApi")
        self.verticalLayout.addWidget(self.labelSelectedApi)
        self.selectedApi = QtWidgets.QComboBox(SettingsWindow)
        self.selectedApi.setObjectName("selectedApi")
        self.selectedApi.addItem("openai")
        self.selectedApi.addItem("anthropic")
        self.selectedApi.addItem("gemini")
        self.verticalLayout.addWidget(self.selectedApi)

        # Emulate
        self.labelEmulate = QtWidgets.QLabel(SettingsWindow)
        self.labelEmulate.setObjectName("labelEmulate")
        self.verticalLayout.addWidget(self.labelEmulate)
        self.emulate = QtWidgets.QComboBox(SettingsWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, 
                                         QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.emulate.sizePolicy().hasHeightForWidth())
        self.emulate.setSizePolicy(sizePolicy)
        self.emulate.setObjectName("emulate")
        self.emulate.addItem("")
        self.emulate.addItem("")
        self.verticalLayout.addWidget(self.emulate)

        # Prompts
        self.addPromptButton = QtWidgets.QPushButton(SettingsWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, 
                                         QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.addPromptButton.sizePolicy().hasHeightForWidth())
        self.addPromptButton.setSizePolicy(sizePolicy)
        self.addPromptButton.setObjectName("addPromptButton")
        self.verticalLayout.addWidget(self.addPromptButton)

        self.scrollArea = QtWidgets.QScrollArea(SettingsWindow)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 779, 605))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.promptsLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.promptsLayout.setObjectName("promptsLayout")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)

        self.saveButton = QtWidgets.QPushButton(SettingsWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, 
                                         QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.saveButton.sizePolicy().hasHeightForWidth())
        self.saveButton.setSizePolicy(sizePolicy)
        self.saveButton.setObjectName("saveButton")
        self.verticalLayout.addWidget(self.saveButton, 0, QtCore.Qt.AlignmentFlag.AlignRight)

        self.retranslateUi(SettingsWindow)
        QtCore.QMetaObject.connectSlotsByName(SettingsWindow)

    def retranslateUi(self, SettingsWindow):
        _translate = QtCore.QCoreApplication.translate
        SettingsWindow.setWindowTitle(_translate("SettingsWindow", "IntelliFiller Settings"))
        self.labelApiKey.setText(_translate("SettingsWindow", "OpenAI API Key:"))
        self.apiKey.setPlaceholderText(_translate("SettingsWindow", "OpenAI API key"))
        self.labelOpenaiModel.setText(_translate("SettingsWindow", "OpenAI Model:"))
        self.openaiModel.setPlaceholderText(_translate("SettingsWindow", "gpt-4o-mini"))
        self.labelAnthropicKey.setText(_translate("SettingsWindow", "Anthropic API Key:"))
        self.anthropicKey.setPlaceholderText(_translate("SettingsWindow", "Anthropic API key"))
        self.labelAnthropicModel.setText(_translate("SettingsWindow", "Anthropic Model:"))
        self.anthropicModel.setPlaceholderText(_translate("SettingsWindow", "claude-haiku-4-5"))
        self.labelGeminiKey.setText(_translate("SettingsWindow", "Google Gemini API Key:"))
        self.geminiKey.setPlaceholderText(_translate("SettingsWindow", "Google Gemini API key"))
        self.labelGeminiModel.setText(_translate("SettingsWindow", "Google Gemini Model:"))
        self.geminiModel.setPlaceholderText(_translate("SettingsWindow", "gemini-2.0-flash-lite-001"))
        self.labelSelectedApi.setText(_translate("SettingsWindow", "Selected API:"))
        self.labelEmulate.setText(_translate("SettingsWindow", "Emulate:"))
        self.emulate.setItemText(0, _translate("SettingsWindow", "yes"))
        self.emulate.setItemText(1, _translate("SettingsWindow", "no"))
        self.addPromptButton.setText(_translate("SettingsWindow", "Add Prompt"))
        self.saveButton.setText(_translate("SettingsWindow", "Save"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    SettingsWindow = QtWidgets.QDialog()
    ui = Ui_SettingsWindow()
    ui.setupUi(SettingsWindow)
    SettingsWindow.show()
    sys.exit(app.exec())