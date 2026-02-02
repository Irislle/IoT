from __future__ import annotations

import logging
import time
from collections import deque
from typing import Deque

from common.models import TemperatureTelemetry
from common.runtime import get_home_catalog_url
from common.service_base import ServiceBase


class TimeShiftProcessor(ServiceBase):
    def __init__(self, home_catalog_url: str) -> None:
        super().__init__("postprocess_time_shift", home_catalog_url)
        self._logger = logging.getLogger("postprocess_time_shift")
        self._window: Deque[float] = deque(maxlen=1)

    def start(self) -> None:
        self.load_config()
        self.connect_mqtt()
        self.mqtt.loop_start()

        window_size = self.service_config["window_size"]
        self._window = deque(maxlen=window_size)
        input_template = self.service_config["input_topic_template"]
        output_template = self.service_config["output_topic_template"]
        rooms = self.service_config["rooms"]

        def handle_message(topic: str, payload: dict) -> None:
            try:
                telemetry = TemperatureTelemetry.from_dict(payload)
            except ValueError as exc:
                self._logger.warning("%s", exc)
                return
            self._window.append(float(telemetry.temp_c))
            avg_temp = sum(self._window) / len(self._window)
            processed = TemperatureTelemetry(
                bn=telemetry.bn,
                ts=int(time.time()),
                room_id=telemetry.room_id,
                temp_c=round(avg_temp, 2),
            ).to_dict()
            output_topic = output_template.format(room_id=telemetry.room_id)
            self.mqtt.publish_json(output_topic, processed)

        input_topics = [(input_template.format(room_id=room_id), 0) for room_id in rooms]
        self.mqtt.subscribe(input_topics, handle_message)
        self._logger.info("Processing %s -> %s", input_template, output_template)
        self.mqtt.loop_forever()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    service = TimeShiftProcessor(home_catalog_url=get_home_catalog_url())
    service.start()


if __name__ == "__main__":
    main()
