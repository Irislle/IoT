# IoT Microservices Platform (MQTT + REST)

This repository provides a reference implementation of the IoT platform described in the architecture diagram, developed for the course **“IoT and Cloud for Sustainable Communities.”** Each component is an independent Python microservice (Python is the primary implementation language) that communicates through MQTT (publish/subscribe) and REST (request/response), with a clear separation between asynchronous telemetry/commands and synchronous configuration queries. Configuration is served at runtime by the Home Catalog REST provider, so you can add or remove devices without changing source code.

This project is **not** a direct copy of the reference example. It adapts the design with an **alert-based control strategy** and an **HVAC-oriented workflow** (cooling/heating commands issued by operators) instead of simple timer-based lighting, aligning the workflow with realistic building management scenarios.

## Architecture overview

**Core communication layers**
- **MQTT (Mosquitto)** for asynchronous telemetry and commands.
- **REST (Home Catalog)** for configuration and service registry.

**Main components**
- **Home Catalog (REST Provider)**: Serves JSON configuration to each service at startup.
- **Device Connector (Raspberry Pi)**: Publishes raw temperature telemetry.
- **Post-process Data Analytics (Time Shift)**: Smooths temperature data and republishes it.
- **Alert & Intervention Strategy**: Active control strategy that evaluates thresholds, applies hysteresis + cooldown, and publishes alert events plus indicator commands.
- **Device Connector (Arduino)**: Subscribes to alert commands and publishes indicator state.
- **Telegram Bot**: User-awareness and optional manual override interface; it is not part of the core control loop.
- **Device Connector (HVAC)**: Applies HVAC commands (issued by the Telegram bot) and publishes state.
- **ThingSpeak Adapter**: Subscribes to MQTT telemetry/state and pushes data to ThingSpeak via REST.
- **Dashboard Consumer (CLI)**: Subscribes to key topics and prints real-time updates for observability.

All exchanged data is JSON with shared identifiers such as `room_id` to correlate across components.

**Shared components (`common/`)**
The `common/` package contains reusable base components that enforce object-oriented design and consistency across services. It provides the MQTT client wrapper, the Home Catalog configuration client, data models, and a base service lifecycle abstraction. Each microservice composes or inherits these elements to reduce duplication and keep behavior aligned with the course’s microservices design principles.

**Scalability and extensibility**
The architecture is intentionally configuration-driven. New rooms, devices, or services can be registered in the Home Catalog JSON configuration, allowing the system to scale to multiple rooms or deployments **without modifying source code**. This design emphasizes extensibility and aligns with academic expectations for maintainable IoT systems.

**Topic conventions and reliability**
Topics are namespaced by room to support multi-room deployments, e.g. `iot/{room_id}/temperature/raw`. Command and state topics use **QoS 1** to improve delivery reliability, and state topics are published with **retain** to expose the latest actuator/indicator status to late subscribers. Each service also advertises an MQTT **LWT** on `iot/services/{service_id}/status` to signal offline/online transitions.

## Quick start

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Run the Home Catalog

```bash
python -m home_catalog.app
```

The Home Catalog reads configuration from `config/home_catalog.json`.

### 3) Run services

Open a new terminal per service. Each service pulls configuration from the Home Catalog at startup.
You can override the default Home Catalog URL (`http://localhost:8000`) by setting the
`HOME_CATALOG_URL` environment variable before starting any service.

```bash
python -m services.rpi_temperature_publisher
python -m services.postprocess_time_shift
python -m services.alert_strategy
python -m services.arduino_indicator
python -m services.telegram_bot_service
python -m services.hvac_connector
python -m services.thingspeak_adapter
python -m services.dashboard_consumer
```

### 4) (Optional) Docker Compose

For a demo environment, start the broker, Home Catalog, and core services with Docker Compose. This is optional and may require building the image and installing dependencies during the first run:

```bash
docker compose up
```

## Configuration

All configuration is centralized in `config/home_catalog.json` and exposed by the Home Catalog REST API. Every service reads:

- MQTT broker host, port, topics
- REST endpoints
- Sampling rates
- Thresholds and cooldowns
- ThingSpeak API key

The configuration format is intentionally extensible: you can register multiple rooms or devices by adding additional service entries and topic mappings in the Home Catalog file. Topic templates (for example, `iot/{room_id}/temperature/raw`) plus a `rooms` list allow multi-room scaling without code edits. This supports exam scenarios where the same microservice logic is reused across several environments without code edits.

The Home Catalog also exposes:
- `GET /services` for service discovery.
- `POST /register` to dynamically register a new service at runtime.

## Data formats

**Temperature telemetry**
```json
{
  "bn": "rpi-1",
  "ts": 1738000000,
  "room_id": "equip-1",
  "temp_c": 25.3,
  "unit": "C"
}
```

**Alert event**
```json
{
  "ts": 1738000005,
  "room_id": "equip-1",
  "type": "OVERHEAT",
  "level": "WARN",
  "temp_c": 26.1
}
```

**Actuator state**
```json
{
  "ts": 1738000010,
  "device": "hvac-1",
  "room_id": "equip-1",
  "state": "ON"
}
```

## Notes
- All components are written with object-oriented Python for clarity and extensibility.
- Non-Python device logic (Arduino/RPi) is intentionally minimal and shown as MQTT connectors.
- Core automation continues to function if the Telegram bot is disabled; the bot only provides user awareness and optional manual override.
- This repository is a runnable reference implementation. Swap any connector with real hardware clients when needed.
