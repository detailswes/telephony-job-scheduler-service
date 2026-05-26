import asyncio
import logging

logger = logging.getLogger(__name__)


async def simulate_twilio_call(phone_number: str, message: str) -> None:
    logger.info(
        "Simulating Twilio call to phone number: %s with message: %s",
        phone_number,
        message,
    )
    await asyncio.sleep(2)
