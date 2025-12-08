import os
import shutil
import time
import uuid
import logging
from pathlib import Path

# Setup simple logger
logger = logging.getLogger(__name__)

def atomic_replace(target_dir: Path, new_content_dir: Path = None) -> bool:
    """
    Performs atomic replacement (or deletions) of target_dir.
    Bypasses Windows file locking by renaming the locked folder.
    
    Args:
        target_dir: Path to the current addon directory (potentially locked).
        new_content_dir: Path to the new version (optional). 
                         If None, acts as atomic_delete (moves to trash).
        
    Returns:
        bool: True on success.
    """
    if not target_dir.exists():
        if new_content_dir and new_content_dir.exists():
            shutil.move(str(new_content_dir), str(target_dir))
        return True

    # Generate unique trash name
    trash_name = f"{target_dir.name}_trash_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    trash_path = target_dir.parent / trash_name

    # STEP 1: Rename current to trash
    try:
        os.rename(target_dir, trash_path)
    except OSError as e:
        # Retry logic for AV scanners
        try:
            time.sleep(0.5)
            os.rename(target_dir, trash_path)
        except OSError as e2:
            raise PermissionError(f"Cannot update addon due to file lock. Restart Anki. {e2}")

    # STEP 2: Move new version into place (if provided)
    if new_content_dir:
        try:
            os.rename(new_content_dir, target_dir)
        except OSError as e:
            # Rollback
            try:
                os.rename(trash_path, target_dir)
            except:
                pass
            raise RuntimeError(f"Update failed during copy: {e}")

    # STEP 3: Best effort cleanup
    try:
        shutil.rmtree(trash_path)
    except OSError:
        # Expected on Windows if files are locked. 
        # Will be cleaned up by _gc_cleanup_trash() on next boot.
        pass
    
    return True
