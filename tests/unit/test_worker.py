from unittest.mock import AsyncMock, patch

import pytest

from app.core.worker import process_job
from app.db.db import add_job, get_job_by_id, init_db


@pytest.mark.asyncio
async def test_process_job_not_found():
    await init_db()
    await process_job(9999)


@pytest.mark.asyncio
async def test_process_job_success():
    await init_db()
    job_id = await add_job("1234567890", "Hello")

    with patch("app.core.worker.simulate_twilio_call", new_callable=AsyncMock):
        with patch("app.core.worker.notify_clients", new_callable=AsyncMock) as notify:
            await process_job(job_id)

    job = await get_job_by_id(job_id)
    assert job["status"] == "completed"
    assert notify.call_count == 2


@pytest.mark.asyncio
async def test_process_job_failure():
    await init_db()
    job_id = await add_job("1234567890", "Hello")

    with patch(
        "app.core.worker.simulate_twilio_call",
        new_callable=AsyncMock,
        side_effect=RuntimeError("call failed"),
    ):
        with patch("app.core.worker.notify_clients", new_callable=AsyncMock):
            with patch("app.core.worker.settings.max_job_retries", 1):
                await process_job(job_id)

    job = await get_job_by_id(job_id)
    assert job["status"] == "failed"
