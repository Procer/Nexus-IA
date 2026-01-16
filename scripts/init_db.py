import asyncio
import sys
import os

# Add the parent directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base
# Import all models so that Base has them registered
from app.models.models import EstudioContable, Cliente, ClienteConexion, Comprobante, ComprobanteIVA, ComprobanteItem

async def init_db():
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables created successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
