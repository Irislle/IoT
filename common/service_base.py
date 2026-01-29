from __future__ import annotations

import logging

from common.config_client import HomeCatalogClient
from common.mqtt_client import MqttConfig, MqttServiceClient


class ServiceBase:
    def __init__(self, service_name: str, home_catalog_url: str) -> None:
        self.service_name = service_name
        self.home_catalog = HomeCatalogClient(home_catalog_url)
        self._logger = logging.getLogger(service_name)
        self._mqtt_client: MqttServiceClient | None = None
        self._service_config: dict | None = None

    @property
    def service_config(self) -> dict:
        if self._service_config is None:
            raise RuntimeError("Service config not loaded")
        return self._service_config

    @property
    def mqtt(self) -> MqttServiceClient:
        if self._mqtt_client is None:
            raise RuntimeError("MQTT client not initialized")
        return self._mqtt_client

    def load_config(self) -> None:
        mqtt_config = self.home_catalog.get_mqtt_config()
        self._service_config = self.home_catalog.get_service_config(self.service_name)
        self._mqtt_client = MqttServiceClient(
            client_id=self.service_name,
            mqtt_config=MqttConfig(**mqtt_config),
        )

    def connect_mqtt(self) -> None:
        self.mqtt.connect()

    def start(self) -> None:
        raise NotImplementedError
