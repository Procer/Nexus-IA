import pytest
from app.services.storage import StorageManager
from pathlib import Path
import shutil
from fastapi import UploadFile
import io
import os

# Mock storage root for testing
TEST_STORAGE_ROOT = "test_storage"

@pytest.fixture
def storage_manager(monkeypatch):
    monkeypatch.setattr("app.services.storage.STORAGE_ROOT", TEST_STORAGE_ROOT)
    # Re-import or ensure we use the mocked path if it was used at module level
    # But storage.py reads env var at top level.
    # monkeypatch.setenv works if called before import, but here it's already imported.
    # We must patch the class constant or the module variable.
    # The module variable STORAGE_ROOT is used in methods.

    # We need to make sure the methods use the new value.
    monkeypatch.setattr("app.services.storage.STORAGE_ROOT", TEST_STORAGE_ROOT)

    yield StorageManager

    # Cleanup
    if Path(TEST_STORAGE_ROOT).exists():
        shutil.rmtree(TEST_STORAGE_ROOT)

@pytest.mark.asyncio
async def test_init_client_storage(storage_manager):
    uuid_cliente = "test-uuid"
    storage_manager.init_client_storage(uuid_cliente)
    path = Path(TEST_STORAGE_ROOT) / "clientes" / uuid_cliente / "vault"
    assert path.exists()

@pytest.mark.asyncio
async def test_save_temp_and_move_to_vault(storage_manager):
    uuid_cliente = "test-uuid"
    file_content = b"test content"
    file = UploadFile(filename="test.pdf", file=io.BytesIO(file_content))

    # 1. Save to temp
    temp_path = await storage_manager.save_temp_file(file)
    assert Path(temp_path).exists()
    assert Path(temp_path).read_bytes() == file_content
    assert "temp" in temp_path

    # 2. Move to vault
    vault_rel_path = storage_manager.move_to_vault(temp_path, uuid_cliente)

    # Resolve absolute path to verify
    vault_abs_path = Path(TEST_STORAGE_ROOT) / vault_rel_path

    assert vault_abs_path.exists()
    assert vault_abs_path.read_bytes() == file_content
    assert "clientes/test-uuid/vault" in str(vault_abs_path)

    # Temp file should be gone
    assert not Path(temp_path).exists()

@pytest.mark.asyncio
async def test_save_file_direct(storage_manager):
    uuid_cliente = "test-uuid"
    file_content = b"direct save"
    file = UploadFile(filename="direct.pdf", file=io.BytesIO(file_content))

    rel_path = await storage_manager.save_file(file, uuid_cliente)
    abs_path = Path(TEST_STORAGE_ROOT) / rel_path

    assert abs_path.exists()
    assert abs_path.read_bytes() == file_content

def test_path_traversal_prevention(storage_manager):
    # Setup a file outside storage root
    outside_file = Path("outside.txt")
    outside_file.touch()

    try:
        # Try to access it via relative path traversal
        with pytest.raises(ValueError, match="Path traversal attempt detected"):
            storage_manager.get_absolute_path("../outside.txt")

        # Try absolute path outside root
        abs_outside = outside_file.resolve()
        with pytest.raises(ValueError, match="Path traversal attempt detected"):
            storage_manager.get_absolute_path(str(abs_outside))

    finally:
        if outside_file.exists():
            outside_file.unlink()
