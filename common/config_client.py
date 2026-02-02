from __future__ import annotations

"""Home Catalog REST client shared by all microservices."""

import requests


class HomeCatalogClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def get_service_config(self, service_name: str) -> dict:
        response = requests.get(f"{self.base_url}/config/{service_name}", timeout=10)
        response.raise_for_status()
        return response.json()

    def get_mqtt_config(self) -> dict:
        response = requests.get(f"{self.base_url}/mqtt", timeout=10)
        response.raise_for_status()
        return response.json()
