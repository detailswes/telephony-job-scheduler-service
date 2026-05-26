import pytest
from pydantic import ValidationError

from app.api.routes import JobRequest


def test_valid_job_request():
    job = JobRequest(phone_number="1234567890", message="Hello")
    assert job.phone_number == "1234567890"
    assert job.message == "Hello"


def test_invalid_phone_number():
    with pytest.raises(ValidationError):
        JobRequest(phone_number="abc", message="Hello")


def test_empty_message():
    with pytest.raises(ValidationError):
        JobRequest(phone_number="1234567890", message="   ")


def test_message_is_sanitized():
    job = JobRequest(phone_number="1234567890", message="<script>alert(1)</script>")
    assert "&lt;script&gt;" in job.message
