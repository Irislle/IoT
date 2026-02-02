from __future__ import annotations

"""Reusable MQTT client wrapper to keep service implementations consistent."""

import json
import logging
import time
from dataclasses import dataclass
from typing import Callable, Iterable

import paho.mqtt.client as mqtt


@dataclass
class MqttConfig:
    host: str
    port: int
    keepalive: int = 60


class MqttServiceClient:
    def __init__(self, client_id: str, mqtt_config: MqttConfig) -> None:
        self._logger = logging.getLogger(client_id)
        self._client = mqtt.Client(client_id=client_id)
        self._config = mqtt_config
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)
        self._status_topic = f"iot/services/{client_id}/status"
        self._client.will_set(
            self._status_topic,
            payload=json.dumps({"status": "OFFLINE", "ts": int(time.time())}),
            qos=1,
            retain=True,
        )

    def connect(self) -> None:
        self._client.connect(self._config.host, self._config.port, self._config.keepalive)

    def loop_forever(self) -> None:
        self._client.loop_forever()

    def loop_start(self) -> None:
        self._client.loop_start()

    def loop_stop(self) -> None:
        self._client.loop_stop()

    def subscribe(self, topics: Iterable[object], handler: Callable[[str, dict], None]) -> None:
        def on_message(client: mqtt.Client, userdata: object, msg: mqtt.MQTTMessage) -> None:
            try:
                payload = json.loads(msg.payload.decode("utf-8"))
                handler(msg.topic, payload)
            except json.JSONDecodeError:
                self._logger.warning("Invalid JSON payload on topic %s", msg.topic)

        self._client.on_message = on_message
        for topic in topics:
            if isinstance(topic, tuple):
                topic_name, qos = topic
            else:
                topic_name, qos = topic, 0
            self._client.subscribe(topic_name, qos=qos)
            self._logger.info("Subscribed to %s (qos=%s)", topic_name, qos)

    def publish_json(self, topic: str, payload: dict, qos: int = 0, retain: bool = False) -> None:
        message = json.dumps(payload, separators=(",", ":"))
        self._client.publish(topic, message, qos=qos, retain=retain)

    def _on_connect(self, client: mqtt.Client, userdata: object, flags: dict, rc: int) -> None:
        if rc == 0:
            self._logger.info("Connected to MQTT broker")
            client.publish(
                self._status_topic,
                json.dumps({"status": "ONLINE", "ts": int(time.time())}),
                qos=1,
                retain=True,
            )
        else:
            self._logger.error("Failed to connect to MQTT broker: %s", rc)

    def _on_disconnect(self, client: mqtt.Client, userdata: object, rc: int) -> None:
        if rc == 0:
            self._logger.info("Disconnected from MQTT broker: %s", rc)
            return
        self._logger.warning("Unexpected MQTT disconnect (rc=%s); attempting reconnect", rc)
        try:
            client.reconnect()
        except Exception as exc:  # pragma: no cover - best-effort reconnect
            self._logger.warning("MQTT reconnect attempt failed: %s", exc)
