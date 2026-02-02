from __future__ import annotations

import logging
import time

from common.models import ActuatorState
from common.runtime import get_home_catalog_url
from common.service_base import ServiceBase


class ArduinoIndicator(ServiceBase):
    def __init__(self, home_catalog_url: str) -> None:
        super().__init__("arduino_indicator", home_catalog_url)
        self._logger = logging.getLogger("arduino_indicator")
        self._state = "OFF"

    def start(self) -> None:
        self.load_config()
        self.connect_mqtt()
        self.mqtt.loop_start()

        command_template = self.service_config["command_topic_template"]
        state_template = self.service_config["state_topic_template"]
        device_id = self.service_config["device_id"]
        room_id = self.service_config["room_id"]
        command_topic = command_template.format(room_id=room_id)
        state_topic = state_template.format(room_id=room_id)

        def handle_message(topic: str, payload: dict) -> None:
            desired_state = payload.get("state", "OFF")
            self._state = desired_state
            reason = payload.get("reason", "N/A")
            self._logger.info("Indicator set to %s (reason=%s)", self._state, reason)
            state_payload = ActuatorState(
                ts=int(time.time()),
                device=device_id,
                room_id=room_id,
                state=self._state,
            ).to_dict()
            self.mqtt.publish_json(state_topic, state_payload, qos=1, retain=True)

        self.mqtt.subscribe([(command_topic, 1)], handle_message)
        self._logger.info("Indicator listening on %s", command_topic)
        self.mqtt.loop_forever()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    service = ArduinoIndicator(home_catalog_url=get_home_catalog_url())
    service.start()


if __name__ == "__main__":
    main()
