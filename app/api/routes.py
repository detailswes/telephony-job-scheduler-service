import html
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Request, Security, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.db.db import add_job, get_job_by_id

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> None:
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )


class JobRequest(BaseModel):
    phone_number: str = Field(
        ...,
        min_length=10,
        max_length=15,
        json_schema_extra={"example": "1234567890"},
    )
    message: str = Field(..., min_length=1, json_schema_extra={"example": "Hello User"})

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not re.fullmatch(r"\+?\d{10,15}", value):
            raise ValueError("Invalid phone number format")
        return value

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message cannot be empty")
        return html.escape(stripped)


class JobResponse(BaseModel):
    job_id: int
    status: str
    created_at: str | None = None
    updated_at: str | None = None


@router.post("/jobs", response_model=JobResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def schedule_job(request: Request, body: JobRequest) -> JobResponse:
    try:
        job_id = await add_job(body.phone_number, body.message)
        job = await get_job_by_id(job_id)
        return JobResponse(
            job_id=job_id,
            status="queued",
            created_at=job["created_at"] if job else None,
            updated_at=job["updated_at"] if job else None,
        )
    except Exception as exc:
        logger.error("Error adding job: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule job due to an internal error",
        ) from exc


@router.get("/jobs/{job_id}", dependencies=[Depends(verify_api_key)])
async def get_job(job_id: int):
    job = await get_job_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job
