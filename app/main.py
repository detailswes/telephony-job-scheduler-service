import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import limiter, router
from app.api.ws import router as ws_router
from app.config import settings
from app.core.worker import job_worker
from app.db.db import close_db, init_db

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    worker_task = asyncio.create_task(job_worker())
    logger.info("Telephony job scheduler started")
    yield
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    await close_db()
    logger.info("Telephony job scheduler stopped")


app = FastAPI(
    title="Telephony Job Scheduler",
    description="Schedule telephony jobs and receive real-time status updates via WebSocket.",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_dict: dict[str, str] = {}

    for err in errors:
        loc = err.get("loc", [])
        if len(loc) == 2 and loc[1] == "phone_number":
            error_dict["phone_number"] = err.get("msg", "Invalid phone number")
        elif len(loc) == 2 and loc[1] == "message":
            error_dict["message"] = err.get("msg", "Invalid message")

    if not error_dict:
        error_dict["error"] = "Invalid request format"

    return JSONResponse(status_code=422, content={"errors": error_dict})


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(router, prefix="/api/v1")
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "telephony-job-scheduler"}
