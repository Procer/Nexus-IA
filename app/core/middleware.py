from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.security import decode_token
import contextvars

# Context variable to store client_id (tenant)
TENANT_ID_CTX_KEY = "client_id"
client_id_context = contextvars.ContextVar(TENANT_ID_CTX_KEY, default=None)

class MultiTenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract client_id from JWT token and set it in context.
    This allows downstream components (like DB sessions or services) to know the current tenant.
    """
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        client_id = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            if payload:
                # We expect the token to contain 'client_id'
                # Use .get() to avoid error if key is missing
                client_id = payload.get("client_id")

        if client_id:
            token_ctx = client_id_context.set(client_id)
            try:
                response = await call_next(request)
            finally:
                client_id_context.reset(token_ctx)
        else:
            # Proceed without client_id.
            # Protected endpoints should use a dependency that checks if client_id is set
            # or validate the token themselves.
            response = await call_next(request)

        return response

def get_current_client_id():
    """Helper to get the current client_id from context."""
    return client_id_context.get()
