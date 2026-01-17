import os
import shutil
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile
import uuid

STORAGE_ROOT = os.getenv("STORAGE_ROOT", "storage")

class StorageManager:
    @staticmethod
    def _get_client_vault_path(uuid_cliente: str, year: int, month: int) -> Path:
        return Path(STORAGE_ROOT) / "clientes" / uuid_cliente / "vault" / str(year) / str(month)

    @staticmethod
    def _get_temp_path() -> Path:
        return Path(STORAGE_ROOT) / "temp"

    @classmethod
    def init_client_storage(cls, uuid_cliente: str):
        """Ensures the base directory structure for a client exists."""
        base_path = Path(STORAGE_ROOT) / "clientes" / uuid_cliente / "vault"
        base_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    async def save_temp_file(cls, file: UploadFile) -> str:
        """
        Saves an uploaded file to the /temp directory with a unique name.
        Returns the absolute path to the temp file.
        """
        temp_dir = cls._get_temp_path()
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Generate a unique filename to prevent collisions and traversal
        file_ext = Path(file.filename).suffix if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = temp_dir / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return str(file_path)

    @classmethod
    def move_to_vault(cls, temp_path_str: str, uuid_cliente: str) -> str:
        """
        Moves a file from temp storage to the client's vault.
        Returns the relative path from STORAGE_ROOT.
        """
        temp_path = Path(temp_path_str)
        if not temp_path.exists():
            raise FileNotFoundError(f"Temp file not found: {temp_path_str}")

        now = datetime.utcnow()
        year = now.year
        month = now.month

        target_dir = cls._get_client_vault_path(uuid_cliente, year, month)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Use the filename from the temp path (which is already a UUID)
        # or we could allow renaming. For now, keeping the UUID filename is safe.
        filename = temp_path.name
        target_path = target_dir / filename

        shutil.move(temp_path, target_path)

        # Return relative path for database storage
        # target_path is absolute if STORAGE_ROOT is absolute?
        # Let's ensure we return relative to STORAGE_ROOT so it's portable.
        return str(target_path.relative_to(Path(STORAGE_ROOT)))

    @classmethod
    async def save_file(cls, file: UploadFile, uuid_cliente: str) -> str:
        """
        Directly saves to vault (legacy/convenience method).
        Securely handles filename.
        """
        # Save to temp first to sanitize and secure
        temp_path = await cls.save_temp_file(file)
        # Then move to vault
        return cls.move_to_vault(temp_path, uuid_cliente)

    @staticmethod
    def get_absolute_path(relative_path: str) -> Path:
        """
        Resolves the relative path to an absolute path and verifies it's within STORAGE_ROOT.
        """
        root = Path(STORAGE_ROOT).resolve()
        # If relative_path is absolute, it ignores root. So we must ensure it's relative or join carefully.
        # But if it's stored in DB as relative, we join.
        # If it's absolute, we check if it starts with root.

        p = Path(relative_path)
        if p.is_absolute():
            abs_path = p.resolve()
        else:
            abs_path = (root / p).resolve()

        if not str(abs_path).startswith(str(root)):
             raise ValueError("Path traversal attempt detected")

        return abs_path
