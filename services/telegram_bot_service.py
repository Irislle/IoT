from __future__ import annotations

"""User-awareness interface for alerts and optional manual HVAC commands."""

import asyncio
import logging
import time
from typing import Optional

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from common.runtime import get_home_catalog_url
from common.service_base import ServiceBase


class TelegramBotService(ServiceBase):
    def __init__(self, home_catalog_url: str) -> None:
        super().__init__("telegram_bot", home_catalog_url)
        self._logger = logging.getLogger("telegram_bot")
        self._chat_id: Optional[str] = None
        self._hvac_state: dict[str, str] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._bot: Optional[Bot] = None

    async def start(self) -> None:
        self.load_config()
        self.connect_mqtt()
        self.mqtt.loop_start()
        self._loop = asyncio.get_running_loop()

        cfg = self.service_config
        self._chat_id = cfg["chat_id"]
        alert_template = cfg["alert_topic_template"]
        hvac_command_template = cfg["hvac_command_topic_template"]
        status_template = cfg["status_topic_template"]
        rooms = cfg["rooms"]

        def handle_alerts(topic: str, payload: dict) -> None:
            if not self._chat_id or self._chat_id == "REPLACE_ME":
                return
            message = (
                f"Alert {payload.get('type')} in {payload.get('room_id')}: "
                f"{payload.get('temp_c')}°C (level {payload.get('level')})"
            )
            if self._loop:
                self._loop.call_soon_threadsafe(asyncio.create_task, self._send_message(message))

        def handle_hvac_state(topic: str, payload: dict) -> None:
            room_id = payload.get("room_id", "unknown")
            state = payload.get("state")
            if state is not None:
                self._hvac_state[room_id] = state

        alert_topics = [(alert_template.format(room_id=room_id), 0) for room_id in rooms]
        status_topics = [(status_template.format(room_id=room_id), 1) for room_id in rooms]
        topic_names = {topic for topic, _ in alert_topics}
        self.mqtt.subscribe(
            alert_topics + status_topics,
            lambda t, p: handle_alerts(t, p) if t in topic_names else handle_hvac_state(t, p),
        )

        app = Application.builder().token(cfg["bot_token"]).build()
        self._bot = app.bot
        app.add_handler(CommandHandler("cooling_on", self._make_hvac_cmd(hvac_command_template, "ON")))
        app.add_handler(CommandHandler("cooling_off", self._make_hvac_cmd(hvac_command_template, "OFF")))
        app.add_handler(CommandHandler("status", self._status))

        self._logger.info("Telegram bot started")
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        await app.updater.idle()

    async def _send_message(self, text: str) -> None:
        if not self._chat_id or self._chat_id == "REPLACE_ME" or not self._bot:
            return
        try:
            await self._bot.send_message(chat_id=self._chat_id, text=text)
        except Exception as exc:  # pragma: no cover - best-effort alerting
            self._logger.warning("Failed to send Telegram message: %s", exc)

    def _make_hvac_cmd(self, topic_template: str, state: str):
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            rooms = self.service_config["rooms"]
            room_id = context.args[0] if context.args else rooms[0]
            if room_id not in rooms:
                await update.message.reply_text(
                    f"Unknown room '{room_id}'. Available rooms: {', '.join(rooms)}"
                )
                return
            payload = {"state": state, "ts": int(time.time()), "room_id": room_id}
            topic = topic_template.format(room_id=room_id)
            self.mqtt.publish_json(topic, payload, qos=1)
            await update.message.reply_text(f"HVAC command sent: {state} for room {room_id}")

        return handler

    async def _status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        rooms = self.service_config["rooms"]
        status_lines = [f"{room_id}: {self._hvac_state.get(room_id, 'UNKNOWN')}" for room_id in rooms]
        await update.message.reply_text("HVAC state:\\n" + "\\n".join(status_lines))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    service = TelegramBotService(home_catalog_url=get_home_catalog_url())
    while True:
        try:
            asyncio.run(service.start())
        except KeyboardInterrupt:
            raise
        except Exception as exc:  # pragma: no cover - retry loop for bot connectivity
            logging.getLogger("telegram_bot").warning(
                "Telegram bot stopped unexpectedly (%s). Retrying in 5s...",
                exc,
            )
            time.sleep(5)


if __name__ == "__main__":
    main()
