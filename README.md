# IoT Microservices Platform (MQTT + REST)

This repository provides a reference implementation of the IoT platform described in the architecture diagram. Each component is an independent Python service that communicates through MQTT (publish/subscribe) and REST (request/response). Configuration is served at runtime by the Home Catalog REST provider, so you can add or remove devices without changing source code.

## Architecture overview

**Core communication layers**
- **MQTT (Mosquitto)** for asynchronous telemetry and commands.
- **REST (Home Catalog)** for configuration and service registry.

**Main components**
- **Home Catalog (REST Provider)**: Serves JSON configuration to each service at startup.
- **Device Connector (Raspberry Pi)**: Publishes raw temperature telemetry.
- **Post-process Data Analytics (Time Shift)**: Smooths temperature data and republishes it.
- **Alert & Intervention Strategy**: Evaluates thresholds, applies hysteresis + cooldown, publishes alert events.
- **Device Connector (Arduino)**: Subscribes to alert commands and publishes indicator state.
- **Telegram Bot**: Notifies operators and publishes HVAC commands.
- **Device Connector (HVAC)**: Applies HVAC commands and publishes state.
- **ThingSpeak Adapter**: Subscribes to MQTT telemetry/state and pushes data to ThingSpeak via REST.

All exchanged data is JSON with shared identifiers such as `room_id` to correlate across components.

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
```

## Configuration

All configuration is centralized in `config/home_catalog.json` and exposed by the Home Catalog REST API. Every service reads:

- MQTT broker host, port, topics
- REST endpoints
- Sampling rates
- Thresholds and cooldowns
- ThingSpeak API key

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
- This repository is a runnable reference implementation. Swap any connector with real hardware clients when needed.
