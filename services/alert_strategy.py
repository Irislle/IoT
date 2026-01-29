from __future__ import annotations

import logging
import time

from common.models import AlertEvent
from common.runtime import get_home_catalog_url
from common.service_base import ServiceBase


class AlertStrategy(ServiceBase):
    """Active control strategy evaluating thresholds and issuing commands."""

    def __init__(self, home_catalog_url: str) -> None:
        super().__init__("alert_strategy", home_catalog_url)
        self._logger = logging.getLogger("alert_strategy")
        self._in_alert = False
        self._last_alert_ts = 0

    def start(self) -> None:
        self.load_config()
        self.connect_mqtt()
        self.mqtt.loop_start()

        cfg = self.service_config
        input_topic = cfg["input_topic"]
        alert_topic = cfg["alert_topic"]
        indicator_topic = cfg["indicator_topic"]
        high_threshold = cfg["high_threshold"]
        low_threshold = cfg["low_threshold"]
        cooldown_s = cfg["cooldown_s"]

        def handle_message(topic: str, payload: dict) -> None:
            temp_c = payload.get("temp_c")
            room_id = payload.get("room_id", "unknown")
            if temp_c is None:
                self._logger.warning("Missing temp_c in payload: %s", payload)
                return

            now = int(time.time())
            if self._in_alert:
                # Remain in alert until temperature drops below the low threshold.
                if temp_c <= low_threshold:
                    self._in_alert = False
                    self._last_alert_ts = now
                    self._publish_alert(room_id, temp_c, "RECOVERED", "INFO", alert_topic)
                    self.mqtt.publish_json(indicator_topic, {"state": "OFF", "room_id": room_id, "ts": now})
                return

            # Trigger an alert state and publish an actuation command when the
            # high threshold is exceeded and cooldown permits.
            if temp_c >= high_threshold and now - self._last_alert_ts >= cooldown_s:
                self._in_alert = True
                self._last_alert_ts = now
                self._publish_alert(room_id, temp_c, "OVERHEAT", "WARN", alert_topic)
                self.mqtt.publish_json(indicator_topic, {"state": "ON", "room_id": room_id, "ts": now})

        self.mqtt.subscribe([input_topic], handle_message)
        self._logger.info("Alert strategy subscribed to %s", input_topic)
        self.mqtt.loop_forever()

    def _publish_alert(self, room_id: str, temp_c: float, alert_type: str, level: str, topic: str) -> None:
        payload = AlertEvent(
            ts=int(time.time()),
            room_id=room_id,
            type=alert_type,
            level=level,
            temp_c=float(temp_c),
        ).to_dict()
        self.mqtt.publish_json(topic, payload)
        self._logger.info("Published alert %s for %s", alert_type, room_id)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    service = AlertStrategy(home_catalog_url=get_home_catalog_url())
    service.start()


if __name__ == "__main__":
    main()
