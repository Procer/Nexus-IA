from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import Comprobante
from app.core.middleware import get_current_client_id
from app.services.storage import StorageManager
import os

router = APIRouter()

@router.get("/stream/{file_id}")
async def stream_file(file_id: int, db: AsyncSession = Depends(get_db)):
    # 1. Get current tenant from context
    current_client_id = get_current_client_id()

    if not current_client_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant context missing")

    try:
        client_id_int = int(current_client_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=403, detail="Invalid client ID in token")

    # 2. Fetch comprobante with strict tenant filtering
    # This prevents ID enumeration by returning 404 if the ID exists but belongs to another client
    stmt = select(Comprobante).where(
        Comprobante.id == file_id,
        Comprobante.client_id == client_id_int
    )
    result = await db.execute(stmt)
    comprobante = result.scalar_one_or_none()

    if not comprobante:
        raise HTTPException(status_code=404, detail="File not found")

    # 3. Serve file
    if not comprobante.file_path:
        raise HTTPException(status_code=404, detail="File path missing")

    try:
        path = StorageManager.get_absolute_path(comprobante.file_path)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not path.exists():
        raise HTTPException(status_code=404, detail="File on disk not found")

    return FileResponse(path)
