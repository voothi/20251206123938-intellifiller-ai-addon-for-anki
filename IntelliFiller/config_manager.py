import os
import json
import shutil
from aqt import mw

class ConfigManager:
    ADDON_DIR = os.path.dirname(__file__)
    USER_FILES_DIR = os.path.join(ADDON_DIR, "user_files")
    SETTINGS_FILE = os.path.join(USER_FILES_DIR, "settings.json")
    CREDENTIALS_FILE = os.path.join(USER_FILES_DIR, "credentials.json")
    PROMPTS_DIR = os.path.join(USER_FILES_DIR, "prompts")

    @classmethod
    def _ensure_directories(cls):
        if not os.path.exists(cls.USER_FILES_DIR):
            os.makedirs(cls.USER_FILES_DIR)
        
        # Ensure we have a dummy file so the folder is included in zip if user zips it manually
        readme = os.path.join(cls.USER_FILES_DIR, "README.txt")
        if not os.path.exists(readme):
             with open(readme, "w", encoding="utf-8") as f:
                 f.write("User data (settings, keys, prompts) is stored here to survive add-on updates.")

        if not os.path.exists(cls.PROMPTS_DIR):
            os.makedirs(cls.PROMPTS_DIR)

    @classmethod
    def load_settings(cls):
        cls._ensure_directories()
        if os.path.exists(cls.SETTINGS_FILE):
             with open(cls.SETTINGS_FILE, "r", encoding="utf-8") as f:
                 return json.load(f)
        return {}

    @classmethod
    def save_settings(cls, data):
        cls._ensure_directories()
        with open(cls.SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    @classmethod
    def load_credentials(cls):
        cls._ensure_directories()
        if os.path.exists(cls.CREDENTIALS_FILE):
             with open(cls.CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                 return json.load(f)
        return {}
    
    @classmethod
    def save_credentials(cls, data):
        cls._ensure_directories()
        with open(cls.CREDENTIALS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    @classmethod
    def list_prompts(cls):
        cls._ensure_directories()
        prompts = []
        if not os.path.exists(cls.PROMPTS_DIR):
            return prompts
            
        for filename in os.listdir(cls.PROMPTS_DIR):
            if filename.endswith(".json"):
                path = os.path.join(cls.PROMPTS_DIR, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Support both single prompt object and list of prompts in one file (if user copies a pack)
                        if isinstance(data, list):
                            prompts.extend(data)
                        elif isinstance(data, dict):
                            prompts.append(data)
                except Exception as e:
                    print(f"Error loading prompt {filename}: {e}")
        return prompts

    @classmethod
    def save_prompt(cls, prompt_data):
        """Saves a single prompt to a file named after its promptName."""
        cls._ensure_directories()
        # Sanitize filename
        safe_name = "".join([c for c in prompt_data["promptName"] if c.isalnum() or c in (' ', '-', '_')]).strip()
        filename = f"{safe_name}.json"
        path = os.path.join(cls.PROMPTS_DIR, filename)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(prompt_data, f, indent=2, sort_keys=True)

    @classmethod
    def delete_prompt_file(cls, prompt_name):
        """Attempts to find and delete the file for a given prompt name."""
        safe_name = "".join([c for c in prompt_name if c.isalnum() or c in (' ', '-', '_')]).strip()
        filename = f"{safe_name}.json"
        path = os.path.join(cls.PROMPTS_DIR, filename)
        if os.path.exists(path):
            os.remove(path)

    @classmethod
    def migrate_legacy_config(cls, addon_name):
        """
        Migrates data from Anki's internal config (meta.json/config.json) to user_files
        IF user_files is empty/missing.
        """
        if os.path.exists(cls.SETTINGS_FILE) or os.path.exists(cls.CREDENTIALS_FILE):
            # Already migrated or in use
            return

        print(f"[{addon_name}] Starting configuration migration to user_files...")
        legacy_config = mw.addonManager.getConfig(addon_name)
        if not legacy_config:
            return

        # 1. Credentials
        cred_keys = [
            "apiKey", "openaiModel", 
            "anthropicKey", "anthropicModel", 
            "geminiKey", "geminiModel", 
            "openrouterKey", "openrouterModel", 
            "customUrl", "customKey", "customModel"
        ]
        credentials = {k: legacy_config.get(k, "") for k in cred_keys}
        cls.save_credentials(credentials)

        # 2. Prompts
        prompts = legacy_config.get("prompts", [])
        for prompt in prompts:
            cls.save_prompt(prompt)

        # 3. Settings (everything else)
        settings = {}
        for k, v in legacy_config.items():
            if k not in cred_keys and k != "prompts":
                settings[k] = v
        
        cls.save_settings(settings)
        print(f"[{addon_name}] Migration complete.")

    @classmethod
    def get_full_config(cls):
        """
        Returns a merged dictionary resembling the old monolithic config.
        Useful for modifying existing code with minimal changes.
        """
        settings = cls.load_settings()
        credentials = cls.load_credentials()
        prompts = cls.list_prompts()
        
        full_config = settings.copy()
        full_config.update(credentials)
        full_config["prompts"] = prompts
        return full_config
