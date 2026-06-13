import os
import shutil
import pytest
from pathlib import Path
from IntelliFiller.atomic_installer import atomic_replace

def test_atomic_replace_target_not_exist(tmp_path):
    # Setup paths
    target_dir = tmp_path / "target_dir"
    new_content_dir = tmp_path / "new_content_dir"
    new_content_dir.mkdir()
    
    # Put a file in new content
    (new_content_dir / "test.txt").write_text("hello", encoding="utf-8")
    
    # Run atomic replace
    success = atomic_replace(target_dir, new_content_dir)
    
    assert success is True
    assert target_dir.exists()
    assert (target_dir / "test.txt").read_text(encoding="utf-8") == "hello"
    assert not new_content_dir.exists()

def test_atomic_replace_success(tmp_path):
    target_dir = tmp_path / "target_dir"
    target_dir.mkdir()
    (target_dir / "__init__.py").write_text("# init", encoding="utf-8")
    (target_dir / "manifest.json").write_text("{}", encoding="utf-8")
    (target_dir / "keep.txt").write_text("keep me in trash then delete", encoding="utf-8")
    
    new_content_dir = tmp_path / "new_content_dir"
    new_content_dir.mkdir()
    (new_content_dir / "new.txt").write_text("new content", encoding="utf-8")
    
    success = atomic_replace(target_dir, new_content_dir)
    
    assert success is True
    assert target_dir.exists()
    assert (target_dir / "new.txt").read_text(encoding="utf-8") == "new content"
    assert not (target_dir / "keep.txt").exists()
    assert not new_content_dir.exists()

def test_atomic_replace_rename_failure_with_retry(mocker, tmp_path):
    target_dir = tmp_path / "target_dir"
    target_dir.mkdir()
    
    new_content_dir = tmp_path / "new_content_dir"
    new_content_dir.mkdir()
    
    mock_sleep = mocker.patch("time.sleep")
    
    # Mock os.rename to fail on the first call, then succeed
    orig_rename = os.rename
    call_count = 0
    
    def side_effect(src, dst):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OSError("Access denied")
        return orig_rename(src, dst)
        
    mocker.patch("os.rename", side_effect=side_effect)
    
    success = atomic_replace(target_dir, new_content_dir)
    
    assert success is True
    mock_sleep.assert_called_once_with(0.5)
    assert target_dir.exists()

def test_atomic_replace_rename_failure_raises(mocker, tmp_path):
    target_dir = tmp_path / "target_dir"
    target_dir.mkdir()
    
    new_content_dir = tmp_path / "new_content_dir"
    new_content_dir.mkdir()
    
    mocker.patch("time.sleep")
    mocker.patch("os.rename", side_effect=OSError("Locked file"))
    
    with pytest.raises(PermissionError) as excinfo:
        atomic_replace(target_dir, new_content_dir)
        
    assert "Cannot update addon due to file lock" in str(excinfo.value)
