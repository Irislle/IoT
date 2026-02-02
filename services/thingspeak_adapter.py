from __future__ import annotations

import logging
from typing import Any, Dict

import requests

from common.runtime import get_home_catalog_url
from common.service_base import ServiceBase


class ThingSpeakAdapter(ServiceBase):
    def __init__(self, home_catalog_url: str) -> None:
        super().__init__("thingspeak_adapter", home_catalog_url)
        self._logger = logging.getLogger("thingspeak_adapter")

    def start(self) -> None:
        self.load_config()
        self.connect_mqtt()
        self.mqtt.loop_start()

        cfg = self.service_config
        topic_templates = cfg["topic_templates"]
        endpoint = cfg["endpoint"]
        api_key = cfg["api_key"]
        rooms = cfg["rooms"]
        topics = [template.format(room_id=room_id) for room_id in rooms for template in topic_templates]
        subscriptions = [(topic, 1 if topic.endswith("/state") else 0) for topic in topics]

        def handle_message(topic: str, payload: dict) -> None:
            data = self._format_payload(api_key, topic, payload)
            if not data:
                return
            try:
                response = requests.post(endpoint, json=data, timeout=10)
                response.raise_for_status()
                self._logger.info("Uploaded data to ThingSpeak for %s", topic)
            except requests.RequestException as exc:
                self._logger.warning("ThingSpeak upload failed: %s", exc)

        self.mqtt.subscribe(subscriptions, handle_message)
        self._logger.info("ThingSpeak adapter subscribed to %s", topics)
        self.mqtt.loop_forever()

    def _format_payload(self, api_key: str, topic: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        data: Dict[str, Any] = {"api_key": api_key, "status": topic}
        if "temp_c" in payload:
            data["field1"] = payload["temp_c"]
        if "state" in payload:
            data["field2"] = payload["state"]
        if "level" in payload:
            data["field3"] = payload["level"]
        if "type" in payload:
            data["field4"] = payload["type"]
        return data


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    service = ThingSpeakAdapter(home_catalog_url=get_home_catalog_url())
    service.start()


if __name__ == "__main__":
    main()
