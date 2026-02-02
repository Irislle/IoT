from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from common.runtime import get_home_catalog_url
from common.service_base import ServiceBase


class DashboardConsumer(ServiceBase):
    """Lightweight CLI dashboard for observability and demos."""

    def __init__(self, home_catalog_url: str) -> None:
        super().__init__("dashboard_consumer", home_catalog_url)
        self._logger = logging.getLogger("dashboard_consumer")

    def start(self) -> None:
        self.load_config()
        self.connect_mqtt()
        self.mqtt.loop_start()

        topic_templates = self.service_config["topic_templates"]
        rooms = self.service_config["rooms"]
        topics = [
            (
                template.format(room_id=room_id),
                1 if template.endswith("/state") else 0,
            )
            for room_id in rooms
            for template in topic_templates
        ]

        def handle_message(topic: str, payload: dict) -> None:
            ts = payload.get("ts")
            timestamp = (
                datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else "n/a"
            )
            self._logger.info(
                "topic=%s ts=%s payload=%s",
                topic,
                timestamp,
                json.dumps(payload, ensure_ascii=False),
            )

        self.mqtt.subscribe(topics, handle_message)
        self._logger.info("Dashboard consumer subscribed to %s", topics)
        self.mqtt.loop_forever()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    service = DashboardConsumer(home_catalog_url=get_home_catalog_url())
    service.start()


if __name__ == "__main__":
    main()
