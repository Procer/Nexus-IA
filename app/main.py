from fastapi import FastAPI
from app.core.middleware import MultiTenantMiddleware
from app.api.endpoints import files

app = FastAPI(title="Nexus IA", version="0.1.0")

# Add the middleware
app.add_middleware(MultiTenantMiddleware)

app.include_router(files.router, prefix="/api/v1/files", tags=["files"])

@app.get("/")
async def root():
    return {"message": "Welcome to Nexus IA"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
