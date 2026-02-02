# IoT Microservices Platform (MQTT + REST)

This repository provides a reference implementation of an IoT microservices platform developed for the course “IoT and Cloud for Sustainable Communities.”
The system is implemented primarily in Python and follows the microservices design pattern required by the course.

Each component runs as an independent microservice and communicates using:

- **MQTT (publish/subscribe)** for asynchronous telemetry, events, and commands
- **REST (request/response)** for configuration retrieval and basic service discovery

Configuration is provided at runtime by a Home Catalog REST service, allowing basic changes (such as adding a new room or device instance) to be performed through configuration rather than by modifying the core service logic.

This project is not a direct copy of the reference example provided during the course.
Instead, it adapts the architecture with an alert-based control strategy and an HVAC-oriented workflow, where alerts are generated automatically and intervention commands (cooling/heating) are issued by an operator. This choice aligns the project with realistic smart-building management scenarios while keeping the overall complexity suitable for a course project.

## Architecture overview

### Core communication layers

- **MQTT (Mosquitto)** for asynchronous telemetry, alerts, and actuation commands
- **REST (Home Catalog)** for configuration distribution and service registry

### Main components

**Home Catalog (REST Provider)**  
Central configuration service that exposes JSON configuration to all microservices at startup.

**Device Connector (Raspberry Pi)**  
Publishes raw temperature telemetry to MQTT.

**Post-process Data Analytics (Time Shift)**  
Applies lightweight smoothing to temperature data and republishes processed values.

**Alert & Intervention Strategy**  
Evaluates processed temperature against thresholds, applies hysteresis and cooldown logic, and publishes alert events and indicator commands.

**Device Connector (Arduino)**  
Subscribes to indicator commands and publishes the resulting indicator state.

**Telegram Bot**  
Provides user awareness and optional manual override; it is not part of the core automation loop.

**Device Connector (HVAC)**  
Applies HVAC commands issued by the operator (via the Telegram bot) and publishes HVAC state.

**ThingSpeak Adapter**  
Subscribes to selected MQTT telemetry/state topics and uploads data to ThingSpeak using REST.

**Dashboard Consumer (CLI)**  
Subscribes to key MQTT topics and prints real-time updates for basic observability.

All exchanged messages use JSON and include shared identifiers such as `room_id` to allow correlation across services.

## Shared components (`common/`)

The `common/` package contains reusable components shared by all services, including:

- an MQTT client wrapper,
- a Home Catalog REST client,
- shared data models,
- a base service lifecycle abstraction.

These components enforce object-oriented design, reduce code duplication, and keep the implementation aligned with the course requirements on microservices and OOP principles.

## Scalability and extensibility

The platform is intentionally configuration-driven.
New rooms, devices, or service instances can be introduced by updating the Home Catalog configuration file, without modifying the microservice source code.

Topic templates (for example, `iot/{room_id}/temperature/raw`) combined with a configurable list of rooms allow the same service logic to be reused across multiple environments. This reflects a common scalability requirement in IoT systems and aligns with the academic objectives of the course.

## Topic conventions and basic robustness

MQTT topics are namespaced by room to support multi-room deployments.
Command and state topics use QoS 1 to avoid losing important messages during testing and demonstrations, and state topics are published with retain so that late subscribers can retrieve the latest actuator or indicator state.

Each service also advertises a simple MQTT Last Will and Testament (LWT) message to signal offline/online transitions. These mechanisms are included to improve robustness in a simple and transparent way and are not required to understand the core system workflow.

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

The Home Catalog reads its configuration from `config/home_catalog.json`.

### 3) Run services

Open a separate terminal for each service. Each microservice retrieves its configuration from the Home Catalog at startup.

The Home Catalog URL defaults to `http://localhost:8000` and can be overridden using the `HOME_CATALOG_URL` environment variable.

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

An optional Docker Compose setup is provided for running the broker, Home Catalog, and core services in a demo environment. This is not required for course evaluation.

```bash
docker compose up
```

## Configuration

All configuration is centralized in `config/home_catalog.json` and exposed through the Home Catalog REST API.
Each service retrieves:

- MQTT broker address and topics
- REST endpoints
- Sampling intervals
- Thresholds and cooldown parameters
- ThingSpeak API key

The configuration format is intentionally extensible and supports multiple rooms or devices by updating configuration entries only.

The Home Catalog also exposes:

- `GET /services` for basic service discovery
- `POST /register` for simple runtime service registration

Dynamic registration is intentionally kept lightweight and in-memory, as the focus of the project is on interaction patterns rather than persistence.

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

- All services are implemented in object-oriented Python.
- Device-side logic (Arduino / Raspberry Pi) is intentionally minimal and modeled as MQTT connectors.
- Core automation continues to function if the Telegram bot is disabled; the bot only provides user awareness and optional manual override.
- This repository provides a runnable reference implementation suitable for course evaluation and experimentation.
