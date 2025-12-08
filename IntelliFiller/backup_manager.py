import os
import shutil
import hashlib
import json
import glob
import datetime
import zipfile
import sys
from pathlib import Path

# Try to import pyzipper for AES encryption
try:
    import pyzipper
    HAS_PYZIPPER = True
except ImportError:
    HAS_PYZIPPER = False

class BackupManager:
    def __init__(self, config_manager, addon_dir):
        self.config_manager = config_manager
        self.addon_dir = addon_dir
        self.manifest_file = os.path.join(addon_dir, 'user_files', 'backup_manifest.json')
        # Ensure user_files exists
        self.user_files_dir = os.path.join(addon_dir, 'user_files')
        if not os.path.exists(self.user_files_dir):
            os.makedirs(self.user_files_dir)

    def load_manifest(self):
        if os.path.exists(self.manifest_file):
            try:
                with open(self.manifest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_manifest(self, manifest):
        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

    def calculate_md5(self, file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def scan_changes(self):
        """
        Scans user_files and root JSON files for changes.
        Returns (has_changes, updated_manifest)
        """
        manifest = self.load_manifest()
        new_manifest = {}
        has_changes = False
        
        # Files to exclude
        excludes_names = ['backup_manifest.json']

        all_items = []

        # 1. user_files (Recursive)
        for root, dirs, files in os.walk(self.user_files_dir):
            for file in files:
                if file in excludes_names: continue
                full_path = os.path.join(root, file)
                # Rel path should start with user_files/ to distinguish
                rel_from_addon = os.path.relpath(full_path, self.addon_dir)
                all_items.append((full_path, rel_from_addon))

        # 2. Root JSON files (Non-recursive, just the specific files)
        # "In general, all json files from this folder"
        root_files = glob.glob(os.path.join(self.addon_dir, "*.json"))
        # Also specifically check if meta.json exists (it might not be a .json if user meant something else, but they said meta.json)
        # User said: "meta.json", "config.json", "config.schema.json", "manifest.json"
        
        for file_path in root_files:
            fname = os.path.basename(file_path)
            if fname in excludes_names: continue
            # Rel path is just filename
            all_items.append((file_path, fname))

        # Check for new or modified files
        for file_path, rel_path in all_items:
            try:
                mtime = os.path.getmtime(file_path)
            except OSError:
                continue

            last_entry = manifest.get(rel_path)
            
            if last_entry and last_entry.get('mtime') == mtime:
                new_manifest[rel_path] = last_entry
            else:
                md5 = self.calculate_md5(file_path)
                if not last_entry or last_entry.get('md5') != md5:
                    has_changes = True
                
                new_manifest[rel_path] = {'mtime': mtime, 'md5': md5}

        # Check for deleted files
        old_files_set = set(manifest.keys())
        current_rel_paths = set(new_manifest.keys())
        
        if old_files_set != current_rel_paths:
             has_changes = True

        return has_changes, new_manifest

    def perform_backup(self, force=False, backup_type='auto'):
        """
        Orchestrates the backup process.
        backup_type: 'auto' (default) or 'manual'
        """
        settings = self.config_manager.load_settings()
        backup_config = settings.get('backup', {})
        
        if not force and not backup_config.get('enabled', False):
            return

        has_changes, new_manifest = self.scan_changes()
        
        # If manual, we proceed even if no changes, unless explicit check wanted.
        # Usually manual means "I want a backup NOW of current state".
        if not force and not has_changes:
            return 

        local_path = backup_config.get('localPath')
        if not local_path:
            return 
            
        if not os.path.exists(local_path):
            try:
                os.makedirs(local_path)
            except:
                return 

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        # New Naming Scheme
        if backup_type == 'manual':
            filename = f"{timestamp}-intellifiller-manual.zip"
        else:
            filename = f"{timestamp}-intellifiller.zip"
            
        target_file = os.path.join(local_path, filename)
        
        password = backup_config.get('zipPassword')
        
        self.create_zip(target_file, password)
        
        self.save_manifest(new_manifest)
        
        external_path = backup_config.get('externalPath')
        if external_path and os.path.isdir(external_path):
             try:
                 shutil.copy2(target_file, os.path.join(external_path, filename))
                 self.prune_backups(external_path, backup_config)
             except:
                 pass

        self.prune_backups(local_path, backup_config)

    def create_zip(self, target_file, password=None):
        """
        Creates a zip file containing user_files (subfolder) and root json files.
        """
        excludes_names = ['backup_manifest.json']
        compression = zipfile.ZIP_DEFLATED
        
        # Collect files to zip mapping: {full_path: arcname}
        files_to_zip = {}
        
        # 1. user_files
        for root, dirs, files in os.walk(self.user_files_dir):
            for file in files:
                if file in excludes_names: continue
                full_path = os.path.join(root, file)
                # Store inside 'user_files/' folder in zip
                rel_from_user_files = os.path.relpath(full_path, self.user_files_dir)
                arcname = os.path.join('user_files', rel_from_user_files)
                files_to_zip[full_path] = arcname
                
        # 2. Root JSONs
        root_files = glob.glob(os.path.join(self.addon_dir, "*.json"))
        for file_path in root_files:
            fname = os.path.basename(file_path)
            if fname in excludes_names: continue
            files_to_zip[file_path] = fname

        def write_to_zip(zf):
             for full_path, arcname in files_to_zip.items():
                try:
                    zf.write(full_path, arcname)
                except:
                    pass

        if password:
            if HAS_PYZIPPER:
                with pyzipper.AESZipFile(target_file, 'w', compression=compression, encryption=pyzipper.WZ_AES) as zf:
                    zf.setpassword(password.encode('utf-8'))
                    write_to_zip(zf)
            else:
                # Security Failure: Standard zipfile cannot encrypt on write (reliably).
                # We must abort to avoid creating an insecure backup when one was requested.
                raise RuntimeError("Cannot create encrypted backup: 'pyzipper' module is missing. Please run scripts/setup_vendor.py")
        else:
            with zipfile.ZipFile(target_file, 'w', compression=compression) as zf:
                 write_to_zip(zf)

    def prune_backups(self, directory, config):
        """
        Implements GFS rotation.
        Ignores manual backups.
        matches: *-intellifiller.zip OR OLD *-intellifiller-backup.zip
        But strictly excludes *-manual.zip
        """
        # Match broader pattern to catch old and new, but filter manual
        pattern = os.path.join(directory, "*.zip")
        all_zips = glob.glob(pattern)
        
        files = []
        for f in all_zips:
            fname = os.path.basename(f)
            # Filter for our files
            is_our_file = ('-intellifiller.zip' in fname) or ('-intellifiller-backup.zip' in fname)
            is_manual = '-manual.zip' in fname
            
            if is_our_file and not is_manual:
                files.append(f)
                
        files.sort() # Sorted by name (timestamp)
        
        if not files:
            return

        now = datetime.datetime.now()
        
        # Parse files into objects
        backups = []
        for f in files:
            try:
                basename = os.path.basename(f)
                ts_str = basename.split('-')[0]
                dt = datetime.datetime.strptime(ts_str, "%Y%m%d%H%M%S")
                backups.append({'path': f, 'dt': dt})
            except:
                continue

        keep_set = set()

        # Helper to find backups within a window
        def get_in_window(duration):
            start = now - duration
            return [b for b in backups if b['dt'] >= start]

        # 1. Keep Monthly (one per month)
        # We need to bucket by Month
        keep_monthly_count = config.get('keepMonthly', 12)
        months_buckets = {}
        for b in backups:
            key = b['dt'].strftime("%Y-%m")
            if key not in months_buckets: months_buckets[key] = []
            months_buckets[key].append(b)
        
        # Sort months desc
        message_keys = sorted(months_buckets.keys(), reverse=True)
        # Keep the *first* (oldest or newest? Usually oldest in the bucket for stability or newest? 
        # GFS usually keeps the one from the beginning of the period. Let's keep the NEWEST for safety.)
        for i, m_key in enumerate(message_keys):
            if i < keep_monthly_count:
                keep_set.add(months_buckets[m_key][-1]['path']) # Keep latest in month

        # 2. Keep Daily (one per day)
        keep_daily_count = config.get('keepDaily', 30)
        day_buckets = {}
        for b in backups:
            key = b['dt'].strftime("%Y-%m-%d")
            if key not in day_buckets: day_buckets[key] = []
            day_buckets[key].append(b)
            
        day_keys = sorted(day_buckets.keys(), reverse=True)
        for i, d_key in enumerate(day_keys):
            if i < keep_daily_count:
                keep_set.add(day_buckets[d_key][-1]['path'])

        # 3. Keep Hourly (one per hour)
        keep_hourly_hours = config.get('keepHourly', 24)
        hour_buckets = {}
        # Only consider recent backups for hourly? Or scan all?
        # Usually GFS is cascading.
        # "Keep all hourly backups for the last 24 hours"
        window_start = now - datetime.timedelta(hours=keep_hourly_hours)
        hourly_candidates = [b for b in backups if b['dt'] >= window_start]
        for b in hourly_candidates:
            key = b['dt'].strftime("%Y-%m-%d %H")
            if key not in hour_buckets: hour_buckets[key] = []
            hour_buckets[key].append(b)
            
        for h_key in hour_buckets:
             keep_set.add(hour_buckets[h_key][-1]['path'])
             
        # 4. Keep 10-minutes
        # "Keep all backups from the last X minutes"? Or one every 10 mins?
        # User said: "часовые, 10 минутные".
        # Let's interpret as: Keep one every 10 minutes for the last hour.
        # Or just keep ALL backups in the last hour?
        # The config says 'keepTenMin' (integer).
        # Let's assume buckets of 10 minutes.
        keep_ten_min_count = config.get('keepTenMin', 6) # e.g. last 60 mins covering 6 intervals
        # Actually simplest interpretation: "Keep snapshots for the last KeepTenMin * 10 minutes"
        # And ensure we have one for each 10-min slot.
        
        ten_min_window = now - datetime.timedelta(minutes=10 * keep_ten_min_count)
        recent_candidates = [b for b in backups if b['dt'] >= ten_min_window]
        
        for b in recent_candidates:
            # Identify 10-min bucket
            minute = b['dt'].minute
            bucket_idx = minute // 10
            key = f"{b['dt'].strftime('%Y-%m-%d %H')}-{bucket_idx}"
            # Actually we likely want to keep ALL in this short window?
            # Or just the latest of each 10 min.
            # Let's keep the latest of each 10 min bucket.
            # But wait, if user modifies file at minute 1 and minute 5, do we want both?
            # Usually strict GFS rotates OUT old copies.
            # Let's keep the latest per 10-min bucket in this window.
            keep_set.add(b['path']) # Actually let's just keep ALL in the recent window. It's safer.
            
        # 5. Keep Yearly
        keep_yearly_count = config.get('keepYearly', 5)
        year_buckets = {}
        for b in backups:
            key = b['dt'].strftime("%Y")
            if key not in year_buckets: year_buckets[key] = []
            year_buckets[key].append(b)
            
        year_keys = sorted(year_buckets.keys(), reverse=True)
        for i, y_key in enumerate(year_keys):
            if i < keep_yearly_count:
                keep_set.add(year_buckets[y_key][-1]['path'])

        # Delete files not in keep_set
        for b in backups:
            if b['path'] not in keep_set:
                try:
                    os.remove(b['path'])
                    print(f"Pruned backup: {b['path']}")
                except:
                    print(f"Failed to prune: {b['path']}")
