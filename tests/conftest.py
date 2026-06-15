import sys
from pathlib import Path
from types import ModuleType

# Add project root to path so we can import IntelliFiller
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock aqt and its submodules
aqt = ModuleType("aqt")
class MockMw:
    class AddonManager:
        def getConfig(self, name):
            return {}
        def setConfigAction(self, name, action):
            pass
    addonManager = AddonManager()
aqt.mw = MockMw()

class DummyQtMetaclass(type):
    def __getattr__(cls, name):
        if name.startswith("__"):
            return super().__getattr__(name)
        return cls

class DummyQtClass(metaclass=DummyQtMetaclass):
    def __init__(self, *args, **kwargs):
        self._val = None
    def __call__(self, *args, **kwargs):
        return self
    def __getattr__(self, name):
        return self
    def connect(self, *args, **kwargs):
        pass
    def emit(self, *args, **kwargs):
        pass
    def setText(self, val):
        self._val = val
    def text(self):
        return self._val if self._val is not None else ""
    def setValue(self, val):
        self._val = val
    def value(self):
        return self._val if self._val is not None else 0
    def setChecked(self, val):
        self._val = val
    def isChecked(self):
        return bool(self._val)
    def setCurrentText(self, val):
        self._val = val
    def currentText(self):
        return self._val if self._val is not None else ""
    def setCurrentData(self, val):
        self._val = val
    def currentData(self):
        return self._val if self._val is not None else ""
    def findData(self, val):
        return 0
    def findText(self, val):
        return 0
    def currentRow(self):
        return -1
    def toPlainText(self):
        return self._val if self._val is not None else ""
    def setPlainText(self, val):
        self._val = val
    def __ge__(self, other):
        return True
    def __gt__(self, other):
        return True
    def __le__(self, other):
        return True
    def __lt__(self, other):
        return True
    def __eq__(self, other):
        return True
    def __ne__(self, other):
        return False
    def __bool__(self):
        return True
    def __int__(self):
        return 0
    def __str__(self):
        return ""
    def __len__(self):
        return 0
    def __iter__(self):
        return iter([])
    class DialogCode:
        Accepted = 1
    class StandardButton:
        Ok = 1
        Cancel = 2
        Save = 0x100
        Discard = 0x200
    class ButtonRole:
        ApplyRole = 3
    class EchoMode:
        Password = 1
        Normal = 2
    class ActionPosition:
        TrailingPosition = 1
    class Orientation:
        Horizontal = 1
    class AlignmentFlag:
        AlignRight = 1
    class Key:
        Key_S = 83
    class KeyboardModifier:
        ControlModifier = 2
    class AbstractItemView:
        class DragDropMode:
            InternalMove = 1

class QtModuleMock(ModuleType):
    def __getattr__(self, name):
        if name.startswith("__"):
            return super().__getattr__(name)
        return DummyQtClass

qt = QtModuleMock("aqt.qt")
qt_names = ["QThread", "pyqtSignal", "QDialog", "QVBoxLayout", "QHBoxLayout", "QProgressBar", 
            "QPushButton", "QLabel", "QLineEdit", "Qt", "QAction", "QStyle", "QApplication", 
            "QIcon", "QTimer", "QWidget", "QFormLayout", "QComboBox", "QSpinBox", "QCheckBox", 
            "QPlainTextEdit", "QListWidget", "QGroupBox", "QDialogButtonBox", "QMenu", "QPoint", 
            "QMessageBox", "QInputDialog", "QFileDialog", "QGuiApplication", "QtCore", "QtGui", 
            "QtWidgets", "QObject", "QEvent", "QAbstractScrollArea"]
qt.__all__ = qt_names
aqt.qt = qt

aqt.gui_hooks = ModuleType("aqt.gui_hooks")
aqt.gui_hooks.editor_did_init_buttons = []
aqt.gui_hooks.profile_will_close = []

aqt.editor = ModuleType("aqt.editor")
aqt.editor.EditorMode = DummyQtClass
aqt.editor.Editor = DummyQtClass

aqt.browser = ModuleType("aqt.browser")
aqt.browser.Browser = DummyQtClass

aqt.addcards = ModuleType("aqt.addcards")
aqt.addcards.AddCards = DummyQtClass

aqt.addons = ModuleType("aqt.addons")
class MockAddonManagerClass:
    def deleteAddon(self, name):
        pass
aqt.addons.AddonManager = MockAddonManagerClass

aqt.utils = ModuleType("aqt.utils")
aqt.utils.showWarning = lambda x: print("Warning:", x)
aqt.utils.showInfo = lambda x: print("Info:", x)

anki = ModuleType("anki")
anki.hooks = ModuleType("anki.hooks")
anki.hooks.addHook = lambda x, y: None

anki_notes = ModuleType("anki.notes")
anki_notes.Note = DummyQtClass
anki_notes.NoteId = DummyQtClass
anki.notes = anki_notes

# Mock openai BEFORE any imports to bypass pydantic loading
openai_mock = ModuleType("openai")
class MockOpenAIClass:
    def __init__(self, **kwargs):
        pass
openai_mock.OpenAI = MockOpenAIClass

# Mock pyzipper and Cryptodome to avoid native loading errors
pyzipper_mock = ModuleType("pyzipper")
pyzipper_mock.AESZipFile = DummyQtClass
pyzipper_mock.WZ_AES = "AES"

cryptodome_mock = ModuleType("Cryptodome")
cryptodome_mock.SelfTest = ModuleType("Cryptodome.SelfTest")

# Register mocks in sys.modules
sys.modules["aqt"] = aqt
sys.modules["aqt.qt"] = qt
sys.modules["aqt.gui_hooks"] = aqt.gui_hooks
sys.modules["aqt.editor"] = aqt.editor
sys.modules["aqt.browser"] = aqt.browser
sys.modules["aqt.addcards"] = aqt.addcards
sys.modules["aqt.addons"] = aqt.addons
sys.modules["aqt.utils"] = aqt.utils
sys.modules["anki"] = anki
sys.modules["anki.hooks"] = anki.hooks
sys.modules["anki.notes"] = anki_notes
sys.modules["openai"] = openai_mock
sys.modules["pyzipper"] = pyzipper_mock
sys.modules["Cryptodome"] = cryptodome_mock

import os
import pytest

@pytest.fixture(autouse=True)
def isolate_config_manager(tmp_path):
    from IntelliFiller.config_manager import ConfigManager
    
    # Store originals
    orig_addon_dir = ConfigManager.ADDON_DIR
    orig_user_files_dir = ConfigManager.USER_FILES_DIR
    orig_settings_file = ConfigManager.SETTINGS_FILE
    orig_credentials_file = ConfigManager.CREDENTIALS_FILE
    orig_prompts_dir = ConfigManager.PROMPTS_DIR
    
    # Set to temp path
    temp_dir = str(tmp_path)
    ConfigManager.ADDON_DIR = temp_dir
    ConfigManager.USER_FILES_DIR = os.path.join(temp_dir, "user_files")
    ConfigManager.SETTINGS_FILE = os.path.join(ConfigManager.USER_FILES_DIR, "settings.json")
    ConfigManager.CREDENTIALS_FILE = os.path.join(ConfigManager.USER_FILES_DIR, "credentials.json")
    ConfigManager.PROMPTS_DIR = os.path.join(ConfigManager.USER_FILES_DIR, "prompts")
    
    # Ensure directories are clean/set up
    ConfigManager._ensure_directories()
    
    yield
    
    # Restore originals
    ConfigManager.ADDON_DIR = orig_addon_dir
    ConfigManager.USER_FILES_DIR = orig_user_files_dir
    ConfigManager.SETTINGS_FILE = orig_settings_file
    ConfigManager.CREDENTIALS_FILE = orig_credentials_file
    ConfigManager.PROMPTS_DIR = orig_prompts_dir

