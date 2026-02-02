from __future__ import annotations

import logging
import time

from common.models import AlertEvent, TemperatureTelemetry
from common.runtime import get_home_catalog_url
from common.service_base import ServiceBase


class AlertStrategy(ServiceBase):
    """Evaluate thresholds and publish alert events plus indicator commands."""

    def __init__(self, home_catalog_url: str) -> None:
        super().__init__("alert_strategy", home_catalog_url)
        self._logger = logging.getLogger("alert_strategy")
        self._in_alert: dict[str, bool] = {}
        self._last_alert_ts: dict[str, int] = {}

    def start(self) -> None:
        self.load_config()
        self.connect_mqtt()
        self.mqtt.loop_start()

        cfg = self.service_config
        input_template = cfg["input_topic_template"]
        alert_template = cfg["alert_topic_template"]
        indicator_template = cfg["indicator_topic_template"]
        high_threshold = cfg["high_threshold"]
        low_threshold = cfg["low_threshold"]
        cooldown_s = cfg["cooldown_s"]
        rooms = cfg["rooms"]

        def handle_message(topic: str, payload: dict) -> None:
            try:
                telemetry = TemperatureTelemetry.from_dict(payload)
            except ValueError as exc:
                self._logger.warning("%s", exc)
                return

            now = int(time.time())
            in_alert = self._in_alert.get(telemetry.room_id, False)
            last_alert_ts = self._last_alert_ts.get(telemetry.room_id, 0)
            if in_alert:
                # Remain in alert until temperature drops below the low threshold.
                if telemetry.temp_c <= low_threshold:
                    self._in_alert[telemetry.room_id] = False
                    self._last_alert_ts[telemetry.room_id] = now
                    alert_topic = alert_template.format(room_id=telemetry.room_id)
                    indicator_topic = indicator_template.format(room_id=telemetry.room_id)
                    self._publish_alert(
                        telemetry.room_id,
                        telemetry.temp_c,
                        "RECOVERED",
                        "INFO",
                        alert_topic,
                    )
                    self.mqtt.publish_json(
                        indicator_topic,
                        {
                            "state": "OFF",
                            "room_id": telemetry.room_id,
                            "ts": now,
                            "reason": "RECOVERED",
                        },
                        qos=1,
                    )
                return

            # Trigger an alert state and publish an indicator command when the
            # high threshold is exceeded and cooldown permits.
            if telemetry.temp_c >= high_threshold and now - last_alert_ts >= cooldown_s:
                self._in_alert[telemetry.room_id] = True
                self._last_alert_ts[telemetry.room_id] = now
                alert_topic = alert_template.format(room_id=telemetry.room_id)
                indicator_topic = indicator_template.format(room_id=telemetry.room_id)
                self._publish_alert(
                    telemetry.room_id,
                    telemetry.temp_c,
                    "OVERHEAT",
                    "WARN",
                    alert_topic,
                )
                self.mqtt.publish_json(
                    indicator_topic,
                    {
                        "state": "ON",
                        "room_id": telemetry.room_id,
                        "ts": now,
                        "reason": "OVERHEAT",
                    },
                    qos=1,
                )

        input_topics = [(input_template.format(room_id=room_id), 0) for room_id in rooms]
        self.mqtt.subscribe(input_topics, handle_message)
        self._logger.info("Alert strategy subscribed to %s", input_template)
        self.mqtt.loop_forever()

    def _publish_alert(self, room_id: str, temp_c: float, alert_type: str, level: str, topic: str) -> None:
        payload = AlertEvent(
            ts=int(time.time()),
            room_id=room_id,
            type=alert_type,
            level=level,
            temp_c=float(temp_c),
        ).to_dict()
        self.mqtt.publish_json(topic, payload, qos=1)
        self._logger.info("Published alert %s for %s", alert_type, room_id)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    service = AlertStrategy(home_catalog_url=get_home_catalog_url())
    service.start()


if __name__ == "__main__":
    main()
