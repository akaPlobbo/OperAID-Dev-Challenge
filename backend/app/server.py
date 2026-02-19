import logging
import asyncio
import os
from datetime import datetime, timezone
from typing import Set, AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from aggregation import Aggregator
from mqtt_client import MQTTClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = "machines/+/scrap"

BASE_DIR = Path(__file__).parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Handle startup and shutdown events."""
    logger.info("Starting MQTT subscriber task...")
    task = asyncio.create_task(mqtt_subscriber())
    yield
    logger.info("Shutting down...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="MQTT Aggregation Dashboard", lifespan=lifespan)

aggregator = Aggregator(window_seconds=60)

connected_clients: Set[WebSocket] = set()


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and register new connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected client."""
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(connection)
        
        for conn in disconnected:
            self.active_connections.discard(conn)


manager = ConnectionManager()


async def process_mqtt_message(payload: dict) -> None:
    """Process incoming MQTT message and broadcast to WebSocket clients."""
    aggregator.add(payload)
    results_df = aggregator.aggregate()

    if results_df.height > 0:
        for row in results_df.to_dicts():
            broadcast_data = {
                "maschinenId": row["maschinenId"],
                "scrapIndex": row["scrapIndex"],
                "sumLast60s": float(row["sumLast60s"]),
                "avgLast60s": round(float(row["avgLast60s"]), 2),
                "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            await manager.broadcast(broadcast_data)


async def mqtt_subscriber():
    """Subscribe to MQTT broker and process messages."""
    while True:
        client = MQTTClient(
            broker=MQTT_BROKER,
            port=MQTT_PORT,
            topic=MQTT_TOPIC,
            on_message=lambda payload: asyncio.create_task(process_mqtt_message(payload))
        )

        try:
            logger.info(f"Starting MQTT subscriber for {MQTT_BROKER}:{MQTT_PORT} ({MQTT_TOPIC})")
            await client.start()
        except asyncio.CancelledError:
            logger.info("MQTT subscriber task cancelled")
            raise
        except Exception as e:
            logger.error(f"MQTT connection error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received from client: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.get("/")
async def root():
    """Serve the dashboard HTML."""
    frontend_file = FRONTEND_DIR / "index.html"
    if not frontend_file.exists():
        return {"error": f"Frontend file not found at {frontend_file}"}
    return FileResponse(frontend_file)


# Mount static files directory
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
else:
    logger.warning(f"Frontend directory not found at {FRONTEND_DIR}")


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "clients_connected": len(manager.active_connections)}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
