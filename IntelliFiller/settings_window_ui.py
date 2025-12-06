# -*- coding: utf-8 -*-

from PyQt6 import QtCore, QtGui, QtWidgets

class Ui_SettingsWindow(object):
    def setupUi(self, SettingsWindow):
        SettingsWindow.setObjectName("SettingsWindow")
        SettingsWindow.setWindowModality(QtCore.Qt.WindowModality.NonModal)
        SettingsWindow.resize(600, 500)
        
        self.verticalLayout = QtWidgets.QVBoxLayout(SettingsWindow)
        self.verticalLayout.setObjectName("verticalLayout")

        self.tabWidget = QtWidgets.QTabWidget(SettingsWindow)
        self.tabWidget.setObjectName("tabWidget")
        
        # --- API Tab ---
        self.tabApi = QtWidgets.QWidget()
        self.tabApi.setObjectName("tabApi")
        self.tabApiLayout = QtWidgets.QVBoxLayout(self.tabApi)
        
        # 1. API Selector at the top
        self.labelSelectedApi = QtWidgets.QLabel(self.tabApi)
        self.selectedApi = QtWidgets.QComboBox(self.tabApi)
        self.selectedApi.addItems(["openai", "anthropic", "gemini", "openrouter", "custom"])
        
        self.apiSelectorLayout = QtWidgets.QFormLayout()
        self.apiSelectorLayout.addRow(self.labelSelectedApi, self.selectedApi)
        self.tabApiLayout.addLayout(self.apiSelectorLayout)
        
        # 2. Stacked Widget for Provider specific fields
        self.stackedWidget = QtWidgets.QStackedWidget(self.tabApi)
        self.tabApiLayout.addWidget(self.stackedWidget)
        
        # Page 0: OpenAI
        self.pageOpenai = QtWidgets.QWidget()
        self.pageOpenaiLayout = QtWidgets.QFormLayout(self.pageOpenai)
        self.labelApiKey = QtWidgets.QLabel(self.pageOpenai)
        self.apiKey = QtWidgets.QLineEdit(self.pageOpenai)
        self.pageOpenaiLayout.addRow(self.labelApiKey, self.apiKey)
        self.labelOpenaiModel = QtWidgets.QLabel(self.pageOpenai)
        self.openaiModel = QtWidgets.QLineEdit(self.pageOpenai)
        self.pageOpenaiLayout.addRow(self.labelOpenaiModel, self.openaiModel)
        self.stackedWidget.addWidget(self.pageOpenai)
        
        # Page 1: Anthropic
        self.pageAnthropic = QtWidgets.QWidget()
        self.pageAnthropicLayout = QtWidgets.QFormLayout(self.pageAnthropic)
        self.labelAnthropicKey = QtWidgets.QLabel(self.pageAnthropic)
        self.anthropicKey = QtWidgets.QLineEdit(self.pageAnthropic)
        self.pageAnthropicLayout.addRow(self.labelAnthropicKey, self.anthropicKey)
        self.labelAnthropicModel = QtWidgets.QLabel(self.pageAnthropic)
        self.anthropicModel = QtWidgets.QLineEdit(self.pageAnthropic)
        self.pageAnthropicLayout.addRow(self.labelAnthropicModel, self.anthropicModel)
        self.stackedWidget.addWidget(self.pageAnthropic)
        
        # Page 2: Gemini
        self.pageGemini = QtWidgets.QWidget()
        self.pageGeminiLayout = QtWidgets.QFormLayout(self.pageGemini)
        self.labelGeminiKey = QtWidgets.QLabel(self.pageGemini)
        self.geminiKey = QtWidgets.QLineEdit(self.pageGemini)
        self.pageGeminiLayout.addRow(self.labelGeminiKey, self.geminiKey)
        self.labelGeminiModel = QtWidgets.QLabel(self.pageGemini)
        self.geminiModel = QtWidgets.QLineEdit(self.pageGemini)
        self.pageGeminiLayout.addRow(self.labelGeminiModel, self.geminiModel)
        self.stackedWidget.addWidget(self.pageGemini)
        
        # Page 3: OpenRouter
        self.pageOpenrouter = QtWidgets.QWidget()
        self.pageOpenrouterLayout = QtWidgets.QFormLayout(self.pageOpenrouter)
        self.labelOpenrouterKey = QtWidgets.QLabel(self.pageOpenrouter)
        self.openrouterKey = QtWidgets.QLineEdit(self.pageOpenrouter)
        self.pageOpenrouterLayout.addRow(self.labelOpenrouterKey, self.openrouterKey)
        self.labelOpenrouterModel = QtWidgets.QLabel(self.pageOpenrouter)
        self.openrouterModel = QtWidgets.QLineEdit(self.pageOpenrouter)
        self.pageOpenrouterLayout.addRow(self.labelOpenrouterModel, self.openrouterModel)
        self.stackedWidget.addWidget(self.pageOpenrouter)
        
        # Page 4: Custom
        self.pageCustom = QtWidgets.QWidget()
        self.pageCustomLayout = QtWidgets.QFormLayout(self.pageCustom)
        self.labelCustomUrl = QtWidgets.QLabel(self.pageCustom)
        self.customUrl = QtWidgets.QLineEdit(self.pageCustom)
        self.pageCustomLayout.addRow(self.labelCustomUrl, self.customUrl)
        self.labelCustomKey = QtWidgets.QLabel(self.pageCustom)
        self.customKey = QtWidgets.QLineEdit(self.pageCustom)
        self.pageCustomLayout.addRow(self.labelCustomKey, self.customKey)
        self.labelCustomModel = QtWidgets.QLabel(self.pageCustom)
        self.customModel = QtWidgets.QLineEdit(self.pageCustom)
        self.pageCustomLayout.addRow(self.labelCustomModel, self.customModel)
        self.stackedWidget.addWidget(self.pageCustom)

        # Emulation (Outside stack, always visible)
        self.emulationLayout = QtWidgets.QFormLayout()
        self.labelEmulate = QtWidgets.QLabel(self.tabApi)
        self.emulate = QtWidgets.QComboBox(self.tabApi)
        self.emulate.addItems(["yes", "no"])
        self.emulationLayout.addRow(self.labelEmulate, self.emulate)
        self.tabApiLayout.addLayout(self.emulationLayout)
        
        # Spacer to push everything up
        self.tabApiLayout.addStretch()

        self.tabWidget.addTab(self.tabApi, "")

        # --- Prompts Tab ---
        self.tabPrompts = QtWidgets.QWidget()
        self.tabPrompts.setObjectName("tabPrompts")
        self.tabPromptsLayout = QtWidgets.QVBoxLayout(self.tabPrompts)

        self.addPromptButton = QtWidgets.QPushButton(self.tabPrompts)
        self.tabPromptsLayout.addWidget(self.addPromptButton)

        self.scrollArea = QtWidgets.QScrollArea(self.tabPrompts)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 500, 300))
        self.promptsLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.tabPromptsLayout.addWidget(self.scrollArea)

        self.tabWidget.addTab(self.tabPrompts, "")
        
        self.verticalLayout.addWidget(self.tabWidget)

        # Save Button
        self.saveButton = QtWidgets.QPushButton(SettingsWindow)
        self.saveButton.setObjectName("saveButton")
        self.verticalLayout.addWidget(self.saveButton, 0, QtCore.Qt.AlignmentFlag.AlignRight)

        self.retranslateUi(SettingsWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(SettingsWindow)

    def retranslateUi(self, SettingsWindow):
        _translate = QtCore.QCoreApplication.translate
        SettingsWindow.setWindowTitle(_translate("SettingsWindow", "IntelliFiller Settings"))
        
        self.labelSelectedApi.setText(_translate("SettingsWindow", "Selected API:"))
        
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
        
        self.labelOpenrouterKey.setText(_translate("SettingsWindow", "OpenRouter API Key:"))
        self.openrouterKey.setPlaceholderText(_translate("SettingsWindow", "OpenRouter API Key"))
        self.labelOpenrouterModel.setText(_translate("SettingsWindow", "OpenRouter Model:"))
        self.openrouterModel.setPlaceholderText(_translate("SettingsWindow", "google/gemini-2.0-flash-lite-001"))
        
        self.labelCustomUrl.setText(_translate("SettingsWindow", "OpenAI Compatible Base URL:"))
        self.customUrl.setPlaceholderText(_translate("SettingsWindow", "https://api.example.com/v1"))
        self.labelCustomKey.setText(_translate("SettingsWindow", "OpenAI Compatible API Key:"))
        self.customKey.setPlaceholderText(_translate("SettingsWindow", "API Key"))
        self.labelCustomModel.setText(_translate("SettingsWindow", "OpenAI Compatible Model ID:"))
        self.customModel.setPlaceholderText(_translate("SettingsWindow", "Model ID"))

        self.labelEmulate.setText(_translate("SettingsWindow", "Emulate:"))
        self.emulate.setItemText(0, _translate("SettingsWindow", "yes"))
        self.emulate.setItemText(1, _translate("SettingsWindow", "no"))
        
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabApi), _translate("SettingsWindow", "API Settings"))
        
        self.addPromptButton.setText(_translate("SettingsWindow", "Add Prompt"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabPrompts), _translate("SettingsWindow", "Prompts"))
        
        self.saveButton.setText(_translate("SettingsWindow", "Save"))