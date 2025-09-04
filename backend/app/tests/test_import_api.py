import io
import pandas as pd
import pytest
from fastapi.testclient import TestClient
import os

# Ensure test mode and auth bypass
os.environ.setdefault("API_AUTH_BYPASS", "true")
os.environ.setdefault("TEST_MODE", "1")

from backend.app.main import app

client = TestClient(app)


def test_import_upload_creates_job(monkeypatch, tmp_path):
    # Patch Celery delay to avoid external broker during tests
    from backend.app.api.routes import imports as imports_route

    called = {}
    def fake_delay(job_id, filepath):
        called["job_id"] = job_id
        called["filepath"] = filepath
    monkeypatch.setattr(imports_route.enqueue_import, "delay", fake_delay)

    # Create minimal xlsx in-memory with required columns
    df = pd.DataFrame([
        {
            "SKU": "ABC-1",
            "Product": "Produto X",
            "Category": "Geral",
            "Price": 10.5,
            "Quantity": 1,
            "Customer Name": "João",
            "Customer Email": "joao@example.com",
            "Sale Date": "01/09/2025",
        }
    ])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)

    files = {"file": ("test.xlsx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = client.post("/import", files=files, headers={"Authorization": "Bearer dev"})
    assert r.status_code == 200, r.text
    job_id = r.json().get("job_id")
    assert job_id
    assert called.get("job_id") == job_id

    # Check status endpoint
    r2 = client.get(f"/import/{job_id}/status", headers={"Authorization": "Bearer dev"})
    assert r2.status_code == 200
    body = r2.json()
    assert body["id"] == job_id
    assert body["status"] in ("PENDING", "RUNNING", "DONE", "FAILED")
