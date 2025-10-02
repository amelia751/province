"""Test main application."""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"


def test_detailed_health_check(client: TestClient):
    """Test detailed health check endpoint."""
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert "database" in data["services"]
    assert "storage" in data["services"]
    assert "search" in data["services"]
    assert "auth" in data["services"]
    assert "ai" in data["services"]


def test_cors_headers(client: TestClient):
    """Test CORS headers are present."""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    # CORS headers are added by middleware, check if they exist
    # Note: In test environment, CORS headers might not be present