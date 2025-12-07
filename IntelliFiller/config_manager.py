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
    
    # Portable hardcoded key (Fallback if user doesn't provide custom salt)
    _DEFAULT_KEY = "IntelliFiller_Portable_Key_2025"

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
    def load_credentials(cls, key=None):
        cls._ensure_directories()
        if not os.path.exists(cls.CREDENTIALS_FILE):
             return {}
        
        # Use provided key or default
        cipher_key = key if key else cls._DEFAULT_KEY

        with open(cls.CREDENTIALS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            
        # Try to decode as Obfuscated first
        try:
            # 1. Base64 Decode
            decoded_bytes = base64.b64decode(content)
            xor_text = decoded_bytes.decode('utf-8')
            # 2. XOR Decrypt
            json_text = cls._xor_cipher(xor_text, cipher_key)
            return json.loads(json_text)
        except:
            # Fallback: Plain JSON (Migration or user disabled obfuscation)
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                print(f"ConfigManager: Failed to load credentials (JSON decode error). Content preview: {content[:20]}...")
                return {}
    
    @classmethod
    def save_credentials(cls, data, key=None, obfuscate=True):
        cls._ensure_directories()
        json_text = json.dumps(data, indent=2, sort_keys=True)
        
        # Use provided key or default
        cipher_key = key if key else cls._DEFAULT_KEY

        if obfuscate:
            # 1. XOR Encrypt
            xor_text = cls._xor_cipher(json_text, cipher_key)
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
        credentials = {}

        # 1. Try to load authoritative config from meta.json first
        meta_path = os.path.join(cls.ADDON_DIR, "meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
                    meta_config = meta_data.get("config", {})
                    # Load credentials from meta.json
                    for k in cred_keys:
                        if k in meta_config:
                            credentials[k] = meta_config[k]
                    print(f"[{addon_name}] Loaded configuration from meta.json (Priority Source).")
            except Exception as e:
                print(f"[{addon_name}] Failed to read meta.json: {e}")

        # 2. Fill missing keys from Anki's current config (fallback/legacy)
        for k in cred_keys:
            if k not in credentials or not credentials[k]:
                 val = legacy_config.get(k, "")
                 if val:
                     credentials[k] = val

        # Default to obfuscated on migration
        print(f"[{addon_name}] Migrating credentials: Found {len([v for v in credentials.values() if v])} non-empty keys.")
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

    @classmethod
    def has_legacy_secrets(cls, addon_name):
        """Checks if legacy files (meta.json/config.json) still contain plain-text secrets."""
        cred_keys = [
            "apiKey", "anthropicKey", "geminiKey", "openrouterKey", "customKey"
        ]
        
        # Check meta.json
        meta_path = os.path.join(cls.ADDON_DIR, "meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    config = data.get("config", {})
                    for k in cred_keys:
                        if config.get(k):
                            return True
            except:
                pass

        # Check config.json (via Anki, or direct read?)
        # Direct read is safer to detect physical file content
        config_path = os.path.join(cls.ADDON_DIR, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k in cred_keys:
                        if data.get(k):
                            return True
            except:
                pass
                
        return False

    @classmethod
    def sanitize_legacy_files(cls, addon_name):
        """Removes secrets from meta.json and config.json."""
        cred_keys = [
            "apiKey", "anthropicKey", "geminiKey", "openrouterKey", "customKey"
        ]
        
        # 1. Sanitize meta.json
        meta_path = os.path.join(cls.ADDON_DIR, "meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                changed = False
                if "config" in data:
                    for k in cred_keys:
                        if data["config"].get(k):
                            data["config"][k] = ""
                            changed = True
                
                if changed:
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    print(f"[{addon_name}] Sanitized meta.json")
            except Exception as e:
                print(f"[{addon_name}] Failed to sanitize meta.json: {e}")

        # 2. Sanitize config.json
        config_path = os.path.join(cls.ADDON_DIR, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                changed = False
                for k in cred_keys:
                    if data.get(k):
                        data[k] = ""
                        changed = True
                
                if changed:
                    with open(config_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    print(f"[{addon_name}] Sanitized config.json")
            except Exception as e:
                print(f"[{addon_name}] Failed to sanitize config.json: {e}")
