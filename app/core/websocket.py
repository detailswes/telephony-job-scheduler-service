import json
import logging

from app.core.broadcast import broadcast

logger = logging.getLogger(__name__)


async def notify_clients(job_id: int, status: str) -> None:
    payload = json.dumps({"job_id": job_id, "status": status})
    display = f"Job {job_id} status: {status}"
    logger.info("Broadcasting job update: %s", payload)
    await broadcast(display)
