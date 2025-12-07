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
        self.selectedApi.addItem("OpenAI", "openai")
        self.selectedApi.addItem("Anthropic", "anthropic")
        self.selectedApi.addItem("Google Gemini", "gemini")
        self.selectedApi.addItem("OpenRouter", "openrouter")
        self.selectedApi.addItem("OpenAI Compatible", "custom")
        
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
        
        self.overwriteFieldLabel = QtWidgets.QLabel(self.tabApi)
        self.overwriteField = QtWidgets.QCheckBox(self.tabApi)
        self.emulationLayout.addRow(self.overwriteFieldLabel, self.overwriteField)
        
        self.flatMenuLabel = QtWidgets.QLabel(self.tabApi)
        self.flatMenu = QtWidgets.QCheckBox(self.tabApi)
        self.emulationLayout.addRow(self.flatMenuLabel, self.flatMenu)
        
        self.labelMaxFavorites = QtWidgets.QLabel(self.tabApi)
        self.maxFavorites = QtWidgets.QSpinBox(self.tabApi)
        self.maxFavorites.setMinimum(0)
        self.maxFavorites.setMaximum(10)
        self.emulationLayout.addRow(self.labelMaxFavorites, self.maxFavorites)

        self.labelObfuscate = QtWidgets.QLabel(self.tabApi)
        self.obfuscateCreds = QtWidgets.QCheckBox(self.tabApi)
        self.emulationLayout.addRow(self.labelObfuscate, self.obfuscateCreds)

        self.labelEncryptionKey = QtWidgets.QLabel(self.tabApi)
        self.encryptionKey = QtWidgets.QLineEdit(self.tabApi)
        self.encryptionKey.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.emulationLayout.addRow(self.labelEncryptionKey, self.encryptionKey)
        
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

        # --- Pipelines Tab ---
        self.tabPipelines = QtWidgets.QWidget()
        self.tabPipelines.setObjectName("tabPipelines")
        self.tabPipelinesLayout = QtWidgets.QHBoxLayout(self.tabPipelines)
        
        # Left: List of Pipelines
        self.pipelinesListLayout = QtWidgets.QVBoxLayout()
        self.pipelinesList = QtWidgets.QListWidget(self.tabPipelines)
        self.pipelinesListLayout.addWidget(self.pipelinesList)
        
        self.addPipelineButton = QtWidgets.QPushButton("Add Pipeline", self.tabPipelines)
        self.pipelinesListLayout.addWidget(self.addPipelineButton)
        self.removePipelineButton = QtWidgets.QPushButton("Remove Pipeline", self.tabPipelines)
        self.pipelinesListLayout.addWidget(self.removePipelineButton)
        
        self.tabPipelinesLayout.addLayout(self.pipelinesListLayout, 1) # Stretch factor 1
        
        # Right: Pipeline Details
        self.pipelineDetailsGroup = QtWidgets.QGroupBox("Pipeline Details", self.tabPipelines)
        self.pipelineDetailsGroup.setEnabled(False) # Disabled initially
        self.pipelineDetailsLayout = QtWidgets.QVBoxLayout(self.pipelineDetailsGroup)
        
        self.pipelineNameLayout = QtWidgets.QHBoxLayout()
        self.labelPipelineName = QtWidgets.QLabel("Name:", self.pipelineDetailsGroup)
        self.pipelineName = QtWidgets.QLineEdit(self.pipelineDetailsGroup)
        self.pipelineNameLayout.addWidget(self.labelPipelineName)
        self.pipelineNameLayout.addWidget(self.pipelineName)
        self.pipelineDetailsLayout.addLayout(self.pipelineNameLayout)
        
        self.pipelinePinnedCheckbox = QtWidgets.QCheckBox("Pin to Menu", self.pipelineDetailsGroup)
        self.pipelineDetailsLayout.addWidget(self.pipelinePinnedCheckbox)
        
        self.labelPipelinePrompts = QtWidgets.QLabel("Prompts in Pipeline (Sequential):", self.pipelineDetailsGroup)
        self.pipelineDetailsLayout.addWidget(self.labelPipelinePrompts)
        
        self.pipelinePromptsList = QtWidgets.QListWidget(self.pipelineDetailsGroup)
        self.pipelinePromptsList.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.pipelineDetailsLayout.addWidget(self.pipelinePromptsList)
        
        self.pipelinePromptsControlsLayout = QtWidgets.QHBoxLayout()
        self.addPromptToPipelineButton = QtWidgets.QPushButton("Add Prompt", self.pipelineDetailsGroup)
        self.removePromptFromPipelineButton = QtWidgets.QPushButton("Remove Prompt", self.pipelineDetailsGroup)
        self.pipelinePromptsControlsLayout.addWidget(self.addPromptToPipelineButton)
        self.pipelinePromptsControlsLayout.addWidget(self.removePromptFromPipelineButton)
        self.pipelineDetailsLayout.addLayout(self.pipelinePromptsControlsLayout)
        
        self.tabPipelinesLayout.addWidget(self.pipelineDetailsGroup, 2) # Stretch factor 2

        self.tabWidget.addTab(self.tabPipelines, "")
        
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
        self.overwriteFieldLabel.setText(_translate("SettingsWindow", "Overwrite Target Field:"))
        self.overwriteField.setText(_translate("SettingsWindow", ""))
        self.flatMenuLabel.setText(_translate("SettingsWindow", "Show in Root Menu:"))
        self.flatMenu.setText(_translate("SettingsWindow", ""))
        self.flatMenu.setToolTip(_translate("SettingsWindow", "If checked, removes the 'IntelliFiller' submenu and shows items directly in the main context menu."))
        self.labelMaxFavorites.setText(_translate("SettingsWindow", "Max Smart Menu Items:"))
        self.labelObfuscate.setText(_translate("SettingsWindow", "Obfuscate Credentials File:"))
        self.obfuscateCreds.setText(_translate("SettingsWindow", ""))
        self.obfuscateCreds.setToolTip(_translate("SettingsWindow", "Encrypts user_files/credentials.json with a reversible cipher to prevent casual reading."))
        self.labelEncryptionKey.setText(_translate("SettingsWindow", "Custom Encryption Salt:"))
        self.encryptionKey.setPlaceholderText(_translate("SettingsWindow", "Leave empty for default portable key"))
        self.encryptionKey.setToolTip(_translate("SettingsWindow", "Custom string used to encrypt the credentials file. If changed, the file will be re-encrypted."))
        
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabApi), _translate("SettingsWindow", "API Settings"))
        
        self.addPromptButton.setText(_translate("SettingsWindow", "Add Prompt"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabPrompts), _translate("SettingsWindow", "Prompts"))
        
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabPipelines), _translate("SettingsWindow", "Pipelines"))
        
        self.saveButton.setText(_translate("SettingsWindow", "Save"))