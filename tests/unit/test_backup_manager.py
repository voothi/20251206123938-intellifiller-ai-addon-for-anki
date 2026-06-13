import os
import json
import datetime
import pytest
from unittest.mock import MagicMock
from freezegun import freeze_time
from IntelliFiller.backup_manager import BackupManager


def _make_backup(directory, ts: datetime.datetime, manual=False, legacy=False):
    """Create a fake zip file in `directory` with the right naming convention."""
    if manual:
        name = ts.strftime("%Y%m%d%H%M%S") + "-intellifiller-manual.zip"
    elif legacy:
        name = ts.strftime("%Y%m%d%H%M%S") + "-intellifiller-backup.zip"
    else:
        name = ts.strftime("%Y%m%d%H%M%S") + "-intellifiller.zip"
    path = os.path.join(directory, name)
    with open(path, "wb") as f:
        f.write(b"PK\x03\x04")  # zip magic
    return path


def _make_addon(tmp_path, with_user_file=True):
    addon_dir = str(tmp_path / "addon")
    user_files = os.path.join(addon_dir, "user_files")
    os.makedirs(user_files, exist_ok=True)
    if with_user_file:
        with open(os.path.join(user_files, "settings.json"), "w", encoding="utf-8") as f:
            json.dump({"selectedApi": "openai"}, f)
    return addon_dir


def _build_manager(addon_dir, local_path, **overrides):
    cm = MagicMock()
    cfg = {
        "backup": {
            "enabled": True,
            "localPath": local_path,
            "zipPassword": None,
            "keepDaily": 7,
            "keepHourly": 24,
            "keepTenMin": 6,
            "keepMonthly": 12,
            "keepYearly": 5,
        }
    }
    if overrides:
        cfg["backup"].update(overrides)
    cm.get_full_config.return_value = cfg
    cm.load_settings.return_value = {}
    return BackupManager(cm, addon_dir)


@pytest.mark.backup
def test_scan_changes_detects_modified_file(tmp_path):
    addon_dir = _make_addon(tmp_path)
    local_path = str(tmp_path / "backups")
    bm = _build_manager(addon_dir, local_path)

    has_changes, manifest = bm.scan_changes()
    assert has_changes is True
    assert "user_files/settings.json" in manifest
    assert "md5" in manifest["user_files/settings.json"]


@pytest.mark.backup
def test_scan_changes_no_changes_on_second_run(tmp_path):
    addon_dir = _make_addon(tmp_path)
    local_path = str(tmp_path / "backups")
    bm = _build_manager(addon_dir, local_path)

    has_changes1, manifest1 = bm.scan_changes()
    bm.save_manifest(manifest1)
    has_changes2, _ = bm.scan_changes()
    assert has_changes1 is True
    assert has_changes2 is False


@pytest.mark.backup
def test_scan_changes_detects_deletion(tmp_path):
    addon_dir = _make_addon(tmp_path)
    local_path = str(tmp_path / "backups")
    bm = _build_manager(addon_dir, local_path)

    _, manifest = bm.scan_changes()
    bm.save_manifest(manifest)
    settings_path = os.path.join(addon_dir, "user_files", "settings.json")
    os.remove(settings_path)

    has_changes, _ = bm.scan_changes()
    assert has_changes is True


@pytest.mark.backup
def test_scan_changes_excludes_signatures_json(tmp_path):
    addon_dir = _make_addon(tmp_path)
    local_path = str(tmp_path / "backups")
    bm = _build_manager(addon_dir, local_path)

    with open(os.path.join(addon_dir, "user_files", "signatures.json"), "w", encoding="utf-8") as f:
        json.dump({"foo": "bar"}, f)

    has_changes, manifest = bm.scan_changes()
    assert "user_files/signatures.json" not in manifest


@pytest.mark.backup
def test_perform_backup_skips_when_disabled_and_not_forced(tmp_path):
    addon_dir = _make_addon(tmp_path)
    local_path = str(tmp_path / "backups")
    cm = MagicMock()
    cm.get_full_config.return_value = {
        "backup": {"enabled": False, "localPath": local_path, "zipPassword": None}
    }
    cm.load_settings.return_value = {}
    bm = BackupManager(cm, addon_dir)
    bm.perform_backup(force=False)
    assert not os.path.exists(local_path)


@pytest.mark.backup
def test_perform_backup_skips_when_no_changes(tmp_path):
    addon_dir = _make_addon(tmp_path, with_user_file=False)
    local_path = str(tmp_path / "backups")
    bm = _build_manager(addon_dir, local_path)
    bm.scan_changes()
    bm.perform_backup(force=False)
    assert not os.path.exists(local_path) or not any(
        f.endswith(".zip") for f in os.listdir(local_path)
    )


@pytest.mark.backup
def test_perform_backup_force_creates_zip_with_password(mocker, tmp_path):
    addon_dir = _make_addon(tmp_path)
    local_path = str(tmp_path / "backups")
    cm = MagicMock()
    cm.get_full_config.return_value = {
        "backup": {
            "enabled": True,
            "localPath": local_path,
            "zipPassword": "secret",
            "keepDaily": 5,
            "keepHourly": 5,
        }
    }
    cm.load_settings.return_value = {}

    def fake_aes(file_path, *args, **kwargs):
        open(file_path, "wb").close()
        return mocker.MagicMock()

    mock_zip = mocker.patch("pyzipper.AESZipFile", side_effect=fake_aes)
    bm = BackupManager(cm, addon_dir)
    bm.perform_backup(force=True, backup_type="manual")

    zips = [f for f in os.listdir(local_path) if f.endswith(".zip")]
    assert len(zips) == 1
    assert "manual" in zips[0]
    mock_zip.assert_called_once()


@pytest.mark.backup
@freeze_time("2026-06-13 12:00:00")
def test_prune_keeps_one_per_day_and_never_manual(tmp_path):
    local_path = str(tmp_path / "backups")
    os.makedirs(local_path, exist_ok=True)
    base = datetime.datetime(2026, 6, 1, 0, 0, 0)
    for day in range(10):
        for hour in range(0, 24, 3):
            ts = base + datetime.timedelta(days=day, hours=hour)
            _make_backup(local_path, ts)
    _make_backup(local_path, base, manual=True)
    _make_backup(local_path, base + datetime.timedelta(days=1, hours=2), manual=True)

    config = {"keepDaily": 3, "keepHourly": 0, "keepTenMin": 0, "keepMonthly": 12, "keepYearly": 5}
    bm = _build_manager(str(tmp_path / "addon"), local_path)
    bm.prune_backups(local_path, config)

    remaining = [f for f in os.listdir(local_path) if f.endswith(".zip")]
    assert any("manual" in f for f in remaining), "manual backups must never be pruned"
    non_manual = [f for f in remaining if "manual" not in f]
    days_kept = {f.split("-")[0][:8] for f in non_manual}
    assert len(days_kept) <= 3


@pytest.mark.backup
@freeze_time("2026-06-13 12:00:00")
def test_prune_keeps_recent_ten_minute_window(tmp_path):
    local_path = str(tmp_path / "backups")
    os.makedirs(local_path, exist_ok=True)
    now = datetime.datetime(2026, 6, 13, 11, 0, 0)
    for minute in range(0, 60, 5):
        _make_backup(local_path, now + datetime.timedelta(minutes=minute))
    for day in range(1, 5):
        _make_backup(local_path, now - datetime.timedelta(days=day))

    config = {"keepDaily": 1, "keepHourly": 0, "keepTenMin": 6, "keepMonthly": 0, "keepYearly": 0}
    bm = _build_manager(str(tmp_path / "addon"), local_path)
    bm.prune_backups(local_path, config)

    remaining = sorted(f for f in os.listdir(local_path) if f.endswith(".zip"))
    assert len(remaining) >= 6
    kept_dates = {f.split("-")[0] for f in remaining}
    assert any(d.startswith("2026061311") for d in kept_dates)


@pytest.mark.backup
@freeze_time("2026-06-13 12:00:00")
def test_prune_keeps_yearly_bucket(tmp_path):
    local_path = str(tmp_path / "backups")
    os.makedirs(local_path, exist_ok=True)
    for year in range(2020, 2026):
        _make_backup(local_path, datetime.datetime(year, 6, 1, 0, 0, 0))

    config = {"keepDaily": 0, "keepHourly": 0, "keepTenMin": 0, "keepMonthly": 0, "keepYearly": 3}
    bm = _build_manager(str(tmp_path / "addon"), local_path)
    bm.prune_backups(local_path, config)

    remaining = [f for f in os.listdir(local_path) if f.endswith(".zip")]
    years_kept = {f[:4] for f in remaining}
    assert years_kept.issubset({"2026", "2025", "2024", "2023"})


@pytest.mark.backup
def test_perform_backup_copies_to_external_path(mocker, tmp_path):
    addon_dir = _make_addon(tmp_path)
    local_path = str(tmp_path / "backups")
    external_path = str(tmp_path / "external")
    os.makedirs(external_path, exist_ok=True)
    cm = MagicMock()
    cm.get_full_config.return_value = {
        "backup": {
            "enabled": True,
            "localPath": local_path,
            "externalPath": external_path,
            "zipPassword": None,
            "keepDaily": 3,
            "keepHourly": 0,
        }
    }
    cm.load_settings.return_value = {}
    bm = BackupManager(cm, addon_dir)
    bm.perform_backup(force=True, backup_type="manual")

    local_zips = [f for f in os.listdir(local_path) if f.endswith(".zip")]
    external_zips = [f for f in os.listdir(external_path) if f.endswith(".zip")]
    assert len(local_zips) == 1
    assert local_zips[0] in os.listdir(external_path)


@pytest.mark.backup
def test_create_zip_unencrypted_uses_zipfile(mocker, tmp_path):
    addon_dir = _make_addon(tmp_path)
    target = str(tmp_path / "out.zip")
    cm = MagicMock()
    cm.get_full_config.return_value = {"backup": {}}
    cm.load_settings.return_value = {}
    bm = BackupManager(cm, addon_dir)

    mock_zf = mocker.MagicMock()
    mock_zipfile = mocker.patch("IntelliFiller.backup_manager.zipfile.ZipFile")
    mock_zipfile.return_value.__enter__.return_value = mock_zf

    bm.create_zip(target, password=None)
    mock_zipfile.assert_called_once()
    assert mock_zf.writestr.called or mock_zf.write.called


@pytest.mark.backup
def test_create_zip_unencrypted_raises_when_pyzipper_missing_and_password_given(mocker, tmp_path):
    addon_dir = _make_addon(tmp_path)
    target = str(tmp_path / "out.zip")
    cm = MagicMock()
    cm.get_full_config.return_value = {"backup": {}}
    cm.load_settings.return_value = {}
    bm = BackupManager(cm, addon_dir)
    mocker.patch("IntelliFiller.backup_manager.HAS_PYZIPPER", False)

    with pytest.raises(RuntimeError, match="pyzipper"):
        bm.create_zip(target, password="x")


@pytest.mark.backup
def test_calculate_md5_is_deterministic(tmp_path):
    addon_dir = _make_addon(tmp_path)
    bm = _build_manager(addon_dir, str(tmp_path / "backups"))
    p = tmp_path / "f.bin"
    p.write_bytes(b"hello world")
    assert bm.calculate_md5(str(p)) == bm.calculate_md5(str(p))


@pytest.mark.backup
def test_load_manifest_missing_returns_empty(tmp_path):
    addon_dir = _make_addon(tmp_path)
    bm = _build_manager(addon_dir, str(tmp_path / "backups"))
    assert bm.load_manifest() == {}


@pytest.mark.backup
def test_save_and_load_manifest_roundtrip(tmp_path):
    addon_dir = _make_addon(tmp_path)
    bm = _build_manager(addon_dir, str(tmp_path / "backups"))
    manifest = {"x.json": {"mtime": 1.0, "md5": "abc"}}
    bm.save_manifest(manifest)
    assert bm.load_manifest() == manifest
