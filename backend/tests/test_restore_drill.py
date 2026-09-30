import os
import tempfile
import pytest
from scripts.backup_db import create_backup
from scripts.restore_drill import run_restore_drill


def test_backup_and_restore_drill_end_to_end():
    """Runs end-to-end backup creation and automated restore verification."""
    with tempfile.TemporaryDirectory() as temp_backup_dir, tempfile.TemporaryDirectory() as temp_restore_dir:
        # 1. Create atomic backup
        backup_path, meta_path, manifest = create_backup(backup_dir=temp_backup_dir)

        assert os.path.exists(backup_path)
        assert os.path.exists(meta_path)
        assert len(manifest["sha256_checksum"]) == 64
        assert manifest["alembic_version"] != "unknown"
        assert len(manifest["table_counts"]) > 0

        # 2. Run restore drill
        target_db = os.path.join(temp_restore_dir, "restored_test.db")
        report = run_restore_drill(backup_path, meta_path, target_db_path=target_db)

        assert report["status"] == "PASSED"
        assert report["checksum_verified"] is True
        assert report["integrity_check"] == "ok"
        assert report["table_counts_verified"] is True
        assert report["canary_queries_passed"] is True
        assert report["duration_ms"] > 0
        assert os.path.exists(target_db)


def test_restore_drill_catches_tampered_backup():
    """Verifies that tampering with a backup file fails checksum validation."""
    with tempfile.TemporaryDirectory() as temp_backup_dir, tempfile.TemporaryDirectory() as temp_restore_dir:
        backup_path, meta_path, manifest = create_backup(backup_dir=temp_backup_dir)

        # Tamper with backup file
        with open(backup_path, "a+b") as f:
            f.write(b"CORRUPTED_BYTES")

        target_db = os.path.join(temp_restore_dir, "restored_tampered.db")
        with pytest.raises(ValueError) as excinfo:
            run_restore_drill(backup_path, meta_path, target_db_path=target_db)

        assert "checksum mismatch" in str(excinfo.value).lower()
