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


def test_atomic_replace_rollback_on_copy_failure(mocker, tmp_path):
    target_dir = tmp_path / "target_dir"
    target_dir.mkdir()
    (target_dir / "old_file.txt").write_text("original", encoding="utf-8")

    new_content_dir = tmp_path / "new_content_dir"
    new_content_dir.mkdir()
    (new_content_dir / "new_file.txt").write_text("new", encoding="utf-8")

    real_rename = os.rename
    call_count = 0

    def selective(src, dst):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise OSError("simulated copy failure")
        return real_rename(src, dst)

    mocker.patch("os.rename", side_effect=selective)
    mocker.patch("time.sleep")
    mocker.patch("shutil.rmtree")

    with pytest.raises(RuntimeError, match="Update failed"):
        atomic_replace(target_dir, new_content_dir)

    assert target_dir.exists()
    assert (target_dir / "old_file.txt").read_text(encoding="utf-8") == "original"


def test_atomic_replace_without_new_content_just_moves_to_trash(mocker, tmp_path):
    target_dir = tmp_path / "target_dir"
    target_dir.mkdir()
    (target_dir / "f.txt").write_text("data", encoding="utf-8")

    real_rename = os.rename
    calls = []

    def tracking(src, dst):
        calls.append((str(src), str(dst)))
        return real_rename(src, dst)

    mocker.patch("os.rename", side_effect=tracking)
    mocker.patch("shutil.rmtree")

    success = atomic_replace(target_dir, None)
    assert success is True
    assert not target_dir.exists()
    assert calls and calls[0][0].endswith("target_dir")
    assert "_trash_" in calls[0][1]


def test_atomic_replace_neutralizes_init_and_manifest(mocker, tmp_path):
    target_dir = tmp_path / "addon"
    target_dir.mkdir()
    (target_dir / "__init__.py").write_text("# init", encoding="utf-8")
    (target_dir / "manifest.json").write_text("{}", encoding="utf-8")
    (target_dir / "keep.py").write_text("keep me", encoding="utf-8")

    new_content_dir = tmp_path / "new"
    new_content_dir.mkdir()
    (new_content_dir / "new.py").write_text("new", encoding="utf-8")

    real_remove = os.remove
    removed = []

    def tracking_remove(p):
        removed.append(str(p))
        return real_remove(p)

    mocker.patch("os.remove", side_effect=tracking_remove)
    mocker.patch("shutil.rmtree")

    success = atomic_replace(target_dir, new_content_dir)
    assert success is True
    assert any("__init__.py" in r for r in removed)
    assert any("manifest.json" in r for r in removed)
    assert not (target_dir / "keep.py").exists()
    assert (target_dir / "new.py").exists()


def test_atomic_replace_continues_when_init_remove_raises(mocker, tmp_path):
    target_dir = tmp_path / "addon"
    target_dir.mkdir()
    (target_dir / "__init__.py").write_text("# init", encoding="utf-8")
    (target_dir / "manifest.json").write_text("{}", encoding="utf-8")

    new_content_dir = tmp_path / "new"
    new_content_dir.mkdir()
    (new_content_dir / "new.py").write_text("new", encoding="utf-8")

    def fail_remove(p):
        if "__init__.py" in str(p) or "manifest.json" in str(p):
            raise OSError("locked")
        return os.remove(p)

    mocker.patch("os.remove", side_effect=fail_remove)
    mocker.patch("shutil.rmtree")

    success = atomic_replace(target_dir, new_content_dir)
    assert success is True
    assert (target_dir / "new.py").exists()


def test_atomic_replace_rollback_swallows_second_failure(mocker, tmp_path):
    target_dir = tmp_path / "addon"
    target_dir.mkdir()
    (target_dir / "old.txt").write_text("old", encoding="utf-8")

    new_content_dir = tmp_path / "new"
    new_content_dir.mkdir()

    real_rename = os.rename
    call_count = 0

    def selective(src, dst):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise OSError("copy failed")
        if call_count == 3:
            raise OSError("rollback also failed")
        return real_rename(src, dst)

    mocker.patch("os.rename", side_effect=selective)
    mocker.patch("time.sleep")
    mocker.patch("shutil.rmtree")

    with pytest.raises(RuntimeError, match="Update failed"):
        atomic_replace(target_dir, new_content_dir)


def test_atomic_replace_trash_cleanup_continues_when_rmtree_fails(mocker, tmp_path):
    target_dir = tmp_path / "addon"
    target_dir.mkdir()
    (target_dir / "f.txt").write_text("data", encoding="utf-8")

    new_content_dir = tmp_path / "new"
    new_content_dir.mkdir()
    (new_content_dir / "new.txt").write_text("new", encoding="utf-8")

    mocker.patch("shutil.rmtree", side_effect=OSError("locked trash"))

    success = atomic_replace(target_dir, new_content_dir)
    assert success is True
    assert (target_dir / "new.txt").exists()


