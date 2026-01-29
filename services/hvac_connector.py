from __future__ import annotations

import logging
import time

from common.models import ActuatorState
from common.runtime import get_home_catalog_url
from common.service_base import ServiceBase


class HvacConnector(ServiceBase):
    def __init__(self, home_catalog_url: str) -> None:
        super().__init__("hvac_connector", home_catalog_url)
        self._logger = logging.getLogger("hvac_connector")
        self._state = "OFF"

    def start(self) -> None:
        self.load_config()
        self.connect_mqtt()
        self.mqtt.loop_start()

        command_topic = self.service_config["command_topic"]
        state_topic = self.service_config["state_topic"]
        device_id = self.service_config["device_id"]
        room_id = self.service_config["room_id"]

        def handle_message(topic: str, payload: dict) -> None:
            desired_state = payload.get("state", "OFF")
            self._state = desired_state
            self._logger.info("HVAC set to %s", self._state)
            state_payload = ActuatorState(
                ts=int(time.time()),
                device=device_id,
                room_id=room_id,
                state=self._state,
            ).to_dict()
            self.mqtt.publish_json(state_topic, state_payload)

        self.mqtt.subscribe([command_topic], handle_message)
        self._logger.info("HVAC listening on %s", command_topic)
        self.mqtt.loop_forever()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    service = HvacConnector(home_catalog_url=get_home_catalog_url())
    service.start()


if __name__ == "__main__":
    main()
