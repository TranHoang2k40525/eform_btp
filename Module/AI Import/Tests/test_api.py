from fastapi.testclient import TestClient

from ai_import.api import app


def test_health_and_model_version():
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    version = client.get("/model/version")
    assert version.status_code == 200
    assert version.json()["strategy"] == "deterministic+fuzzy+optional-embedding"

