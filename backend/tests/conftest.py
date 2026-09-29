import pytest
import os
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure test settings before importing app
os.environ["ENVIRONMENT"] = "testing"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["UPLOAD_DIR"] = "data/test_uploads"
os.environ["CHROMA_PERSIST_DIR"] = "data/test_vectorstore"

from app.main import app
from app.core.config import settings


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_dirs():
    yield
    # Cleanup after tests
    import shutil
    test_upload = settings.BASE_DIR / "data/test_uploads"
    test_chroma = settings.BASE_DIR / "data/test_vectorstore"
    if test_upload.exists():
        shutil.rmtree(test_upload, ignore_errors=True)
    if test_chroma.exists():
        shutil.rmtree(test_chroma, ignore_errors=True)
