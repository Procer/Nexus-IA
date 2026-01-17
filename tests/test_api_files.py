from fastapi.testclient import TestClient
from app.main import app
from app.core.middleware import get_current_client_id
from app.core.database import get_db
import pytest
from unittest.mock import MagicMock, patch

# We need to override the dependency get_db and also mock the auth
# Since we are using an async DB, testing with TestClient (which is sync) against async endpoints
# that use async DB session requires `TestClient` or `AsyncClient`.
# However, mocking the DB session is often easier for unit tests of endpoints.

@pytest.fixture
def mock_db_session():
    return MagicMock()

def test_stream_file_unauthorized():
    client = TestClient(app)
    # No auth header
    response = client.get("/api/v1/files/stream/1")
    # Our middleware passes request but context is empty.
    # Endpoint checks context.
    assert response.status_code == 401
    assert response.json() == {"detail": "Tenant context missing"}

def test_stream_file_success():
    # We need to generate a valid token or mock the middleware/context
    # Mocking contextvars is tricky in async.
    # But since TestClient runs in same thread usually...
    # Better: Mock `app.core.middleware.decode_token` to return a payload.

    with patch("app.core.middleware.decode_token") as mock_decode:
        mock_decode.return_value = {"client_id": 123}

        # Also need to mock DB
        # Since we don't have a real DB running, we must mock `get_db`
        # or use an in-memory SQLite (but we use aiomysql driver which requires MySQL).
        # So we mock the dependency.

        with patch("app.api.endpoints.files.get_db") as mock_get_db:
            # Setup mock db session
            mock_session = MagicMock()
            mock_result = MagicMock()

            # Mock the scalar_one_or_none result
            mock_comprobante = MagicMock()
            mock_comprobante.file_path = "test.pdf"
            mock_comprobante.client_id = 123

            mock_result.scalar_one_or_none.return_value = mock_comprobante

            # Async mock for execute
            async def async_execute(*args, **kwargs):
                return mock_result

            mock_session.execute.side_effect = async_execute

            # Async generator for get_db
            async def override_get_db():
                yield mock_session

            app.dependency_overrides[get_db] = override_get_db

            # Mock StorageManager to avoid file system
            with patch("app.api.endpoints.files.StorageManager") as MockStorage:
                MockStorage.get_absolute_path.return_value.exists.return_value = True
                # We need to return a Path-like object that FileResponse accepts
                # FileResponse checks path is file.
                # It's better to point to a real file in test
                import pathlib
                MockStorage.get_absolute_path.return_value = pathlib.Path(__file__)

                client = TestClient(app)
                headers = {"Authorization": "Bearer fake-token"}
                response = client.get("/api/v1/files/stream/1", headers=headers)

                assert response.status_code == 200
                # Content should be this file's content

            # Cleanup
            app.dependency_overrides = {}

def test_stream_file_not_found_or_access_denied():
    with patch("app.core.middleware.decode_token") as mock_decode:
        mock_decode.return_value = {"client_id": 123}

        with patch("app.api.endpoints.files.get_db") as mock_get_db:
            mock_session = MagicMock()
            mock_result = MagicMock()
            # Return None (not found or filtered out)
            mock_result.scalar_one_or_none.return_value = None

            async def async_execute(*args, **kwargs):
                return mock_result
            mock_session.execute.side_effect = async_execute

            async def override_get_db():
                yield mock_session
            app.dependency_overrides[get_db] = override_get_db

            client = TestClient(app)
            headers = {"Authorization": "Bearer fake-token"}
            response = client.get("/api/v1/files/stream/1", headers=headers)

            assert response.status_code == 404

            app.dependency_overrides = {}
