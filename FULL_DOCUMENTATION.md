# IoT Microservices Platform — Full Code & Architecture Documentation

This document consolidates the **overall framework structure** and a **code-level walkthrough** of each module in the project. It is intended for academic review and exam submission to make the architecture, responsibilities, and implementation details explicit.

## 1) Repository Structure (Conceptual Overview)

```
/workspace/IoT
├── README.md
├── requirements.txt
├── config/
│   └── home_catalog.json
├── home_catalog/
│   └── app.py
├── common/
│   ├── config_client.py
│   ├── mqtt_client.py
│   ├── models.py
│   ├── runtime.py
│   └── service_base.py
└── services/
    ├── rpi_temperature_publisher.py
    ├── postprocess_time_shift.py
    ├── alert_strategy.py
    ├── arduino_indicator.py
    ├── telegram_bot_service.py
    ├── hvac_connector.py
    ├── thingspeak_adapter.py
    └── dashboard_consumer.py
```

## 2) Core Architectural Principles

- **Microservices architecture**: each Python file in `services/` is an independent process.
- **MQTT for telemetry & commands**: asynchronous publish/subscribe for sensor data and actuator control.
- **REST for configuration**: the Home Catalog exposes JSON configuration that every service retrieves at runtime.
- **OOP reuse through `common/`**: shared configuration client, MQTT wrapper, data models, and base lifecycle.

## 3) Configuration & Home Catalog (REST)

### `config/home_catalog.json`
Defines the MQTT broker information and per-service configuration. Examples include:
- MQTT host/port/keepalive
- topic templates for raw/processed temperature (e.g. `iot/{room_id}/temperature/raw`)
- alert thresholds + cooldown
- Telegram and ThingSpeak credentials
Room lists (`rooms`) enable multi-room subscriptions without code changes.

### `home_catalog/app.py`
A minimal FastAPI service exposing:
- `GET /mqtt` → returns broker config
- `GET /config/{service_name}` → returns service-specific JSON config
- `GET /services` → returns registered service names
- `POST /register` → dynamically register a new service

## 4) Shared Package (`common/`)

### `common/config_client.py`
A reusable REST client for the Home Catalog. All microservices call:
- `get_mqtt_config()`
- `get_service_config(service_name)`

### `common/mqtt_client.py`
A simple MQTT wrapper around `paho-mqtt` with:
- connection handling + LWT service status topics
- automatic reconnect with bounded backoff
- JSON publish helper (QoS + retain support)
- JSON decode + subscription helper

### `common/models.py`
Shared data structures for JSON payloads:
- `TemperatureTelemetry`
- `AlertEvent`
- `ActuatorState`
Each model also provides `from_dict` validation for basic schema checks.

### `common/service_base.py`
Base class that standardizes:
- loading configuration
- MQTT initialization
- consistent lifecycle startup

### `common/runtime.py`
Centralized runtime helper to read `HOME_CATALOG_URL` (with default fallback).

## 5) Microservices (`services/`)

### `rpi_temperature_publisher.py`
- Simulates or reads sensor data
- Publishes **raw temperature telemetry** to MQTT
- Example payload: `{bn, ts, room_id, temp_c, unit}`

### `postprocess_time_shift.py`
- Subscribes to raw temperature topic
- Applies windowed smoothing
- Publishes **processed temperature** to a new topic

### `alert_strategy.py`
- Active control strategy
- Subscribes to processed temperature
- Applies **threshold + hysteresis + cooldown**
- Publishes alert events and indicator commands (no automatic HVAC actuation)

### `arduino_indicator.py`
- Subscribes to alert indicator commands
- Simulates a local LED/relay state
- Publishes indicator state back to MQTT

### `telegram_bot_service.py`
- User awareness / optional manual override interface
- Receives alerts and notifies operators
- Publishes HVAC commands on demand (manual user action)
- Not part of the core control loop (system runs without it)
- Includes a retry loop to handle temporary Telegram connectivity issues

### `hvac_connector.py`
- Subscribes to HVAC commands
- Applies actuator state (simulated)
- Publishes HVAC state via MQTT

### `thingspeak_adapter.py`
- Subscribes to telemetry/state topics
- Pushes data to ThingSpeak via REST

### `dashboard_consumer.py`
- Lightweight CLI dashboard for observability
- Subscribes to telemetry/alerts/state topics and prints updates

## 6) End-to-End Data Flow Summary

1. RPi connector publishes **raw temperature** → MQTT
2. Post-processor smooths and republishes → MQTT
3. Alert strategy evaluates and publishes **alerts + indicator commands** → MQTT
4. Arduino indicator updates local state → MQTT
5. Telegram bot notifies users / sends manual HVAC commands → MQTT
6. HVAC connector applies the requested HVAC command and reports state → MQTT
7. ThingSpeak adapter logs telemetry/state via REST

## 7) How to Run (Single-Sentence Reminder)

Start the Home Catalog, then launch each service as its own process; all configuration is retrieved dynamically from the REST catalog.

## 8) Reproducible Environment (Optional)

`docker-compose.yml` provides a minimal stack with Mosquitto, the Home Catalog, and core services to help reproduce the visible data flow in a consistent way.
