"""MQTT client to subscribe to machine scrap data."""
import json
import logging
import asyncio
from typing import Callable, Optional
import aiomqtt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MQTTClient:
    """Reusable MQTT client with callback support."""

    def __init__(
        self,
        broker: str,
        port: int,
        topic: str,
        on_message: Optional[Callable[[dict], object]] = None
    ):
        """Initialize MQTT client.
        
        Args:
            broker: MQTT broker hostname
            port: MQTT broker port
            topic: Topic pattern to subscribe to
            on_message: Callback function to handle received messages
        """
        self.broker = broker
        self.port = port
        self.topic = topic
        self.on_message = on_message or self._default_handler

    def _default_handler(self, payload: dict) -> None:
        """Default message handler that logs to console."""
        logger.info(f"Received: {payload}")

    async def start(self) -> None:
        """Connect to broker and start processing messages."""
        try:
            logger.info(f"Connecting to MQTT broker at {self.broker}:{self.port}...")
            async with aiomqtt.Client(hostname=self.broker, port=self.port) as client:
                await client.subscribe(self.topic)
                logger.info(f"Subscribed to topic: {self.topic}")

                async for message in client.messages:
                    try:
                        payload = json.loads(message.payload.decode())
                        logger.info(f"[{message.topic}] {payload}")
                        self.on_message(payload)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON: {message.payload} - {e}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")

        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            raise


async def main():
    """Run standalone MQTT subscriber for testing."""
    client = MQTTClient(
        broker="localhost",
        port=1883,
        topic="machines/+/scrap"
    )
    
    try:
        logger.info("Waiting for messages. Press Ctrl+C to stop\n")
        await client.start()
    except KeyboardInterrupt:
        logger.info("\nStopping subscriber...")


if __name__ == "__main__":
    asyncio.run(main())
