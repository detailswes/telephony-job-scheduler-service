import asyncio
import logging

from app.config import settings
from app.core.twilio_simulator import simulate_twilio_call
from app.core.websocket import notify_clients
from app.db.db import claim_queued_jobs, get_job_by_id, update_job_status

logger = logging.getLogger(__name__)


async def process_job(job_id: int) -> None:
    job = await get_job_by_id(job_id)
    if job is None:
        logger.error("Job %d not found, skipping", job_id)
        return

    await update_job_status(job_id, "processing")
    await notify_clients(job_id, "processing")

    for attempt in range(1, settings.max_job_retries + 1):
        try:
            logger.info("Processing job id: %d (attempt %d)", job_id, attempt)
            await simulate_twilio_call(job["phone_number"], job["message"])
            logger.info("Process completed for job id: %d", job_id)
            await update_job_status(job_id, "completed")
            await notify_clients(job_id, "completed")
            return
        except Exception as exc:
            logger.error("Job %d failed on attempt %d: %s", job_id, attempt, exc)
            if attempt == settings.max_job_retries:
                await update_job_status(job_id, "failed")
                await notify_clients(job_id, "failed")
            else:
                await asyncio.sleep(2**attempt)


async def _run_with_sem(sem: asyncio.Semaphore, job_id: int) -> None:
    async with sem:
        await process_job(job_id)


async def job_worker() -> None:
    sem = asyncio.Semaphore(settings.max_concurrent_jobs)

    while True:
        try:
            claimed_ids = await claim_queued_jobs(limit=settings.max_concurrent_jobs)
            if claimed_ids:
                tasks = [
                    asyncio.create_task(_run_with_sem(sem, job_id)) for job_id in claimed_ids
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as exc:
            logger.error("Worker loop error: %s", exc)

        await asyncio.sleep(settings.worker_poll_interval)
