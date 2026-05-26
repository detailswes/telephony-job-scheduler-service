import time

import pytest
from starlette.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.db.db import init_db
from app.main import app


@pytest.mark.asyncio
async def test_websocket_receives_job_update(auth_headers):
    await init_db()

    with patch("app.core.worker.simulate_twilio_call", new_callable=AsyncMock):
        with TestClient(app) as client:
            with client.websocket_connect("/ws/jobs") as websocket:
                response = client.post(
                    "/api/v1/jobs",
                    json={"phone_number": "1234567890", "message": "Hello"},
                    headers=auth_headers,
                )
                assert response.status_code == 200
                job_id = response.json()["job_id"]

                messages = []
                deadline = time.time() + 10
                while len(messages) < 2 and time.time() < deadline:
                    messages.append(websocket.receive_text())

                assert any(f"Job {job_id} status: processing" in msg for msg in messages)
                assert any(f"Job {job_id} status: completed" in msg for msg in messages)
