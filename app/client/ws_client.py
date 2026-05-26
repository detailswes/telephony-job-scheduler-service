import asyncio
import websockets
from websockets.exceptions import ConnectionClosedError, InvalidStatusCode

async def listen():
    url = "ws://localhost:8000/ws/jobs"
    max_retries = 5
    retry_delay = 1
    retry_count = 0

    while retry_count < max_retries:
        try:
            async with websockets.connect(url) as ws:
                print(f"Connected to WebSocket server at {url}")
                # Reset retry count on successful connection
                retry_count = 0
                retry_delay = 1
                while True:
                    try:
                        msg = await ws.recv()
                        print(f"Received: {msg}")
                    except ConnectionClosedError as e:
                        print(f"Connection closed by server: {e}")
                        break
            # Outside the websocket context but inside the try block
            # Wait before attempting to reconnect
            retry_count += 1
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)  # Exponential backoff capped at 60 seconds
        except ConnectionRefusedError:
            print("Could not connect to WebSocket server. Is it running?")
            retry_count += 1
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)
        except InvalidStatusCode as e:
            print(f"Failed to connect: Invalid response status code ({e.status_code})")
            retry_count += 1
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)
        except Exception as e:
            print(f"Unexpected error: {e}")
            retry_count += 1
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)
    print(f"Maximum retries ({max_retries}) exceeded. Giving up.")

if __name__ == "__main__":
    try:
        asyncio.run(listen())
    except KeyboardInterrupt:
        print("\nWebSocket client terminated by user.")