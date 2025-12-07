import os
import json
import shutil
import base64
from aqt import mw

class ConfigManager:
    ADDON_DIR = os.path.dirname(__file__)
    USER_FILES_DIR = os.path.join(ADDON_DIR, "user_files")
    SETTINGS_FILE = os.path.join(USER_FILES_DIR, "settings.json")
    CREDENTIALS_FILE = os.path.join(USER_FILES_DIR, "credentials.json")
    PROMPTS_DIR = os.path.join(USER_FILES_DIR, "prompts")
    
    # Portable hardcoded key (Security against casual observation, not crypto-analysis)
    _SECRET_KEY = "IntelliFiller_Portable_Key_2025"

    @classmethod
    def _write_file_safely(cls, path, content_str):
        """Atomic write: Write to .tmp then rename."""
        tmp_path = path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(content_str)
            # Atomic replacement
            if os.path.exists(path):
                os.replace(tmp_path, path)
            else:
                os.rename(tmp_path, path)
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise e

    @classmethod
    def _xor_cipher(cls, text, key):
        """Simple XOR cipher for obfuscation."""
        return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text))

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
        content = json.dumps(data, indent=2, sort_keys=True)
        cls._write_file_safely(cls.SETTINGS_FILE, content)

    @classmethod
    def load_credentials(cls):
        cls._ensure_directories()
        if not os.path.exists(cls.CREDENTIALS_FILE):
             return {}
        
        with open(cls.CREDENTIALS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            
        # Try to decode as Obfuscated first
        try:
            # 1. Base64 Decode
            decoded_bytes = base64.b64decode(content)
            xor_text = decoded_bytes.decode('utf-8')
            # 2. XOR Decrypt
            json_text = cls._xor_cipher(xor_text, cls._SECRET_KEY)
            return json.load(json_text)
        except:
            # Fallback: Plain JSON (Migration or user disabled obfuscation)
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {}
    
    @classmethod
    def save_credentials(cls, data, obfuscate=True):
        cls._ensure_directories()
        json_text = json.dumps(data, indent=2, sort_keys=True)
        
        if obfuscate:
            # 1. XOR Encrypt
            xor_text = cls._xor_cipher(json_text, cls._SECRET_KEY)
            # 2. Base64 Encode (to make it safe text string)
            encoded_bytes = base64.b64encode(xor_text.encode('utf-8'))
            final_content = encoded_bytes.decode('utf-8')
        else:
            final_content = json_text
            
        cls._write_file_safely(cls.CREDENTIALS_FILE, final_content)

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
        
        content = json.dumps(prompt_data, indent=2, sort_keys=True)
        cls._write_file_safely(path, content)

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
        # Default to obfuscated on migration
        cls.save_credentials(credentials, obfuscate=True)

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
