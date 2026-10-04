import os
import tempfile
from pathlib import Path
import pytest
from sqlalchemy import text
from app.db.session import get_engine, DBWrapper
from alembic.config import Config
from alembic import command
from app.core.settings import settings
from fastapi.testclient import TestClient
from app.database import init_database
from app.main import app

@pytest.fixture(autouse=True, scope="session")
def setup_database():
    backend_dir = Path(__file__).resolve().parent.parent
    alembic_ini = backend_dir / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))
    
    # Must explicitly set script_location because cwd might be wrong
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    
    engine = get_engine()
    with engine.begin() as connection:
        alembic_cfg.attributes['connection'] = connection
        command.upgrade(alembic_cfg, "head")
    
    yield


@pytest.fixture
def client():
    original_database_path = settings.DATABASE_PATH
    try:
        with tempfile.TemporaryDirectory() as database_directory:
            settings.DATABASE_PATH = str(Path(database_directory) / "test_recommendations.db")
            init_database()

            with TestClient(app) as test_client:
                yield test_client
    finally:
        settings.DATABASE_PATH = original_database_path
