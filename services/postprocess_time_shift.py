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
        input_topic = self.service_config["input_topic"]
        output_topic = self.service_config["output_topic"]

        def handle_message(topic: str, payload: dict) -> None:
            temp_c = payload.get("temp_c")
            if temp_c is None:
                self._logger.warning("Missing temp_c in payload: %s", payload)
                return
            self._window.append(float(temp_c))
            avg_temp = sum(self._window) / len(self._window)
            processed = TemperatureTelemetry(
                bn=payload.get("bn", "rpi-unknown"),
                ts=int(time.time()),
                room_id=payload.get("room_id", "unknown"),
                temp_c=round(avg_temp, 2),
            ).to_dict()
            self.mqtt.publish_json(output_topic, processed)

        self.mqtt.subscribe([input_topic], handle_message)
        self._logger.info("Processing %s -> %s", input_topic, output_topic)
        self.mqtt.loop_forever()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    service = TimeShiftProcessor(home_catalog_url=get_home_catalog_url())
    service.start()


if __name__ == "__main__":
    main()
