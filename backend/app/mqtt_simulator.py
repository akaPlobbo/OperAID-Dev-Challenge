import aiomqtt
import asyncio
import json
import random
import os
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = "machines"
MACHINES = ["A1", "B1", "C1"]
INDICES = [1, 2, 3]

def generate_data(machine_id: str, scrap_index: int):
    """Generate machine sensor data with UTC timestamp."""
    return {
        "maschinenId": machine_id,
        "scrapeIndex": scrap_index,
        "value": round(random.uniform(1.0, 5.0), 2),
        "zeitstempel": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    }

async def main():
    """Run MQTT simulator."""
    try:
        logger.info(f"Connecting to MQTT broker at {BROKER}:{PORT}...")
        async with aiomqtt.Client(hostname=BROKER, port=PORT) as client:
            logger.info(f"Connected to MQTT broker at {BROKER}:{PORT}")
            logger.info("Starting data simulation...")
            logger.info(f"Machines: {MACHINES}")
            logger.info(f"Scrap indices: {INDICES}")
            logger.info("Press Ctrl+C to stop\n")
            
            counter = 0
            
            while True:
                machine_id = random.choice(MACHINES)
                scrap_index = random.choice(INDICES)
                
                data = generate_data(machine_id, scrap_index)
                
                topic = f"{TOPIC}/{machine_id}/scrap"
                payload = json.dumps(data)
                
                await client.publish(topic, payload)
                counter += 1
                
                logger.info(f"[{counter}] Published to {topic}: {payload}")
                await asyncio.sleep(random.uniform(0.5, 2.0))
                
    except KeyboardInterrupt:
        logger.info("\nStopping simulator...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        logger.info("Simulator stopped")


if __name__ == "__main__":
    asyncio.run(main())
