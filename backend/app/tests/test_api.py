import os
import io
import json
import pytest

# Ensure auth bypass before app import
os.environ.setdefault("API_AUTH_BYPASS", "true")
os.environ.setdefault("TEST_MODE", "1")

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200


def test_auth_verify_bypass():
    r = client.post("/auth/verify", headers={"Authorization": "Bearer dev"})
    assert r.status_code == 200
    assert r.json().get("ok") is True
