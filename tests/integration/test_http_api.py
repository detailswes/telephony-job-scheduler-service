import pytest

from app.db.db import add_job, init_db


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_schedule_job_success(client, auth_headers):
    await init_db()
    response = await client.post(
        "/api/v1/jobs",
        json={"phone_number": "1234567890", "message": "Hello User"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert "job_id" in data


@pytest.mark.asyncio
async def test_schedule_job_invalid_phone(client, auth_headers):
    response = await client.post(
        "/api/v1/jobs",
        json={"phone_number": "invalid", "message": "Hello"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_schedule_job_empty_message(client, auth_headers):
    response = await client.post(
        "/api/v1/jobs",
        json={"phone_number": "1234567890", "message": "   "},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_schedule_job_missing_api_key(client):
    response = await client.post(
        "/api/v1/jobs",
        json={"phone_number": "1234567890", "message": "Hello"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_job(client, auth_headers):
    await init_db()
    create_response = await client.post(
        "/api/v1/jobs",
        json={"phone_number": "1234567890", "message": "Hello"},
        headers=auth_headers,
    )
    job_id = create_response.json()["job_id"]

    response = await client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == job_id


@pytest.mark.asyncio
async def test_get_job_not_found(client, auth_headers):
    await init_db()
    response = await client.get("/api/v1/jobs/9999", headers=auth_headers)
    assert response.status_code == 404
