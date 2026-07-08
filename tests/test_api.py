"""Integration tests for API endpoints."""

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["docs"] == "/docs"


@pytest.mark.asyncio
async def test_create_ticket():
    """Test ticket creation endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        ticket_data = {
            "subject": "Test ticket",
            "body": "This is a test ticket for integration testing",
            "source": "api",
        }
        response = await client.post("/api/v1/tickets", json=ticket_data)
        assert response.status_code == 201
        data = response.json()
        assert data["subject"] == ticket_data["subject"]
        assert data["status"] == "open"
        assert "id" in data


@pytest.mark.asyncio
async def test_list_tickets():
    """Test ticket listing endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/tickets")
        assert response.status_code == 200
        data = response.json()
        assert "tickets" in data
        assert "total" in data
        assert isinstance(data["tickets"], list)


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test metrics endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_tickets" in data
        assert "tickets_by_status" in data
        assert "automation_rate" in data
