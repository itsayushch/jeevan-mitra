import os
import tempfile

from fastapi.testclient import TestClient

from app.config import settings
from app.database import init_database
from app.main import app


def test_journey_ownership_uses_authenticated_session_token():
    original_database_path = settings.DATABASE_PATH
    database_directory = tempfile.TemporaryDirectory()
    settings.DATABASE_PATH = os.path.join(database_directory.name, "journey.db")
    init_database()

    try:
        with TestClient(app) as client:
            session = client.post("/api/v1/sessions").json()
            session_headers = {"X-Session-Token": session["session_token"]}
            started = client.post(
                "/api/v1/journey/start",
                json={"actor_id": "forged-owner", "actor_role": "admin"},
                headers=session_headers
            )
            assert started.status_code == 200
            journey_id = started.json()["id"]

            owned = client.get(f"/api/v1/journey/{journey_id}", headers=session_headers)
            assert owned.status_code == 200
            assert owned.json()["actor_id"] == session["session_id"]
            assert owned.json()["actor_role"] == "anonymous"

            other_session = client.post("/api/v1/sessions").json()
            other_headers = {"X-Session-Token": other_session["session_token"]}
            stolen = client.get(
                f"/api/v1/journey/{journey_id}?actor_id={session['session_id']}",
                headers=other_headers
            )
            assert stolen.status_code == 400
    finally:
        settings.DATABASE_PATH = original_database_path
        database_directory.cleanup()
