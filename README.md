# OperAID-Dev-Challenge
Live-Dashboard für MQTT-Maschinendaten mit **FastAPI**, **WebSocket**, **Polars** und **Chart.js**.  
Es werden Werte pro Maschine und Scrap-Index über ein gleitendes 60-Sekunden-Fenster aggregiert (Summe + Durchschnitt).

## Features

- MQTT-Subscription auf `machines/+/scrap`
- Live-Aggregation (letzte 60 Sekunden)
- Echtzeit-Updates per WebSocket (`/ws`)
- Dashboard mit Karten + Balkendiagramm
- Docker-Setup mit Mosquitto Broker + App

## Projektstruktur

- [docker-compose.yml](docker-compose.yml)
- [Dockerfile](Dockerfile)
- [requirements.txt](requirements.txt)
- [backend/app/server.py](backend/app/server.py)
- [backend/app/aggregation.py](backend/app/aggregation.py)
- [backend/app/mqtt_client.py](backend/app/mqtt_client.py)
- [backend/app/mqtt_simulator.py](backend/app/mqtt_simulator.py)
- [frontend/index.html](frontend/index.html)
- [frontend/app.js](frontend/app.js)
- [frontend/styles.css](frontend/styles.css)
- [mosquitto/config/mosquitto.conf](mosquitto/config/mosquitto.conf)

## Architektur (kurz)

1. [backend/app/mqtt_simulator.py](backend/app/mqtt_simulator.py) publiziert Testdaten an Mosquitto.
2. [`mqtt_client.MQTTClient`](backend/app/mqtt_client.py) empfängt MQTT-Nachrichten.
3. [`aggregation.Aggregator`](backend/app/aggregation.py) aggregiert Werte über 60 Sekunden.
4. [`server.ConnectionManager.broadcast`](backend/app/server.py) sendet Ergebnisse an WebSocket-Clients.
5. [frontend/app.js](frontend/app.js) rendert Karten + Chart.js-Balkendiagramm.

## Voraussetzungen

- Docker + Docker Compose  
**oder**
- Python 3.11+

## Schnellstart mit Docker

```bash
docker compose up --build
```

Danach:

- Dashboard: http://localhost:8000
- Health: http://localhost:8000/api/health
- MQTT Broker: `localhost:1883`
- MQTT WebSockets (Broker): `localhost:9001`

Stoppen:

```bash
docker compose down
```

## Lokaler Start ohne Docker (optional)

### 1) Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 2) Mosquitto starten

Nutze einen lokalen Broker mit Konfiguration aus  
[mosquitto/config/mosquitto.conf](mosquitto/config/mosquitto.conf).

### 3) Backend starten

```bash
python backend/app/server.py
```

### 4) Simulator starten (zweites Terminal)

```bash
python backend/app/mqtt_simulator.py
```

## Datenformat

Der Aggregator akzeptiert folgende Felder (mehrsprachig/tolerant):

- Maschine: `machineId` oder `maschinenId`
- Index: `scrapIndex` oder `scrapeIndex`
- Wert: `value`
- Zeit: `timestamp` oder `zeitstempel`

Beispiel-Payload:

```json
{
  "maschinenId": "A1",
  "scrapeIndex": 2,
  "value": 4,
  "zeitstempel": "2026-01-01T12:00:00Z"
}
```

## API & Echtzeit

- `GET /` → Dashboard HTML aus [frontend/index.html](frontend/index.html)
- `GET /api/health` → Status + Anzahl WebSocket-Clients
- `WS /ws` → Echtzeit-Aggregate für das Frontend

Beispiel-WS-Nachricht vom Server:

```json
{
  "maschinenId": "A1",
  "scrapIndex": 2,
  "sumLast60s": 25.0,
  "avgLast60s": 3.57,
  "timestamp": "2026-01-01T12:00:30Z"
}
```

## Hinweise

- Die App nutzt standardmäßig:
  - `MQTT_BROKER=localhost`
  - `MQTT_PORT=1883`
- In Docker werden diese Variablen in [docker-compose.yml](docker-compose.yml) gesetzt.
- Startlogik der Container-App ist in [Dockerfile](Dockerfile) definiert.

## Relevante Kernstellen im Code

- Aggregation: [`aggregation.Aggregator.aggregate`](backend/app/aggregation.py)
- MQTT Subscribe Loop: [`server.mqtt_subscriber`](backend/app/server.py)
- WebSocket Endpoint: [`server.websocket_endpoint`](backend/app/server.py)
- Frontend Rendering: [frontend/app.js](frontend/app.js)