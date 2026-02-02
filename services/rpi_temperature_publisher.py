from __future__ import annotations

import logging
import random
import time

from common.models import TemperatureTelemetry
from common.runtime import get_home_catalog_url
from common.service_base import ServiceBase


class TemperaturePublisher(ServiceBase):
    def __init__(self, home_catalog_url: str) -> None:
        super().__init__("rpi_temperature_publisher", home_catalog_url)
        self._logger = logging.getLogger("rpi_temperature_publisher")

    def start(self) -> None:
        self.load_config()
        self.connect_mqtt()
        self.mqtt.loop_start()

        topic_template = self.service_config["topic_template"]
        sampling_s = self.service_config["sampling_s"]
        room_id = self.service_config["room_id"]
        device_id = self.service_config["device_id"]

        topic = topic_template.format(room_id=room_id)
        self._logger.info("Publishing temperature telemetry to %s", topic)
        while True:
            now = int(time.time())
            temp_c = round(random.uniform(23.5, 27.5), 2)
            payload = TemperatureTelemetry(
                bn=device_id,
                ts=now,
                room_id=room_id,
                temp_c=temp_c,
            ).to_dict()
            self.mqtt.publish_json(topic, payload)
            time.sleep(sampling_s)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    service = TemperaturePublisher(home_catalog_url=get_home_catalog_url())
    service.start()


if __name__ == "__main__":
    main()
