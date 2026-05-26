import pytest

from app.db.db import add_job, claim_queued_jobs, get_job_by_id, init_db, update_job_status


@pytest.mark.asyncio
async def test_add_and_get_job():
    await init_db()
    job_id = await add_job("1234567890", "Test message")
    job = await get_job_by_id(job_id)

    assert job is not None
    assert job["phone_number"] == "1234567890"
    assert job["message"] == "Test message"
    assert job["status"] == "queued"
    assert job["created_at"] is not None
    assert job["updated_at"] is not None


@pytest.mark.asyncio
async def test_update_job_status():
    await init_db()
    job_id = await add_job("1234567890", "Test message")
    await update_job_status(job_id, "processing")
    job = await get_job_by_id(job_id)
    assert job["status"] == "processing"


@pytest.mark.asyncio
async def test_claim_queued_jobs():
    await init_db()
    job_id = await add_job("1234567890", "Test message")
    claimed = await claim_queued_jobs(limit=5)

    assert job_id in claimed
    job = await get_job_by_id(job_id)
    assert job["status"] == "claimed"
