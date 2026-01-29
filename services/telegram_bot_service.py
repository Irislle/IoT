from __future__ import annotations

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
        self._hvac_state: Optional[str] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._bot: Optional[Bot] = None

    async def start(self) -> None:
        self.load_config()
        self.connect_mqtt()
        self.mqtt.loop_start()
        self._loop = asyncio.get_running_loop()

        cfg = self.service_config
        self._chat_id = cfg["chat_id"]
        alert_topic = cfg["alert_topic"]
        hvac_command_topic = cfg["hvac_command_topic"]
        status_topic = cfg["status_topic"]

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
            self._hvac_state = payload.get("state")

        self.mqtt.subscribe(
            [alert_topic, status_topic],
            lambda t, p: handle_alerts(t, p) if t == alert_topic else handle_hvac_state(t, p),
        )

        app = Application.builder().token(cfg["bot_token"]).build()
        self._bot = app.bot
        app.add_handler(CommandHandler("cooling_on", self._make_hvac_cmd(hvac_command_topic, "ON")))
        app.add_handler(CommandHandler("cooling_off", self._make_hvac_cmd(hvac_command_topic, "OFF")))
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

    def _make_hvac_cmd(self, topic: str, state: str):
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            payload = {"state": state, "ts": int(time.time())}
            self.mqtt.publish_json(topic, payload)
            await update.message.reply_text(f"HVAC command sent: {state}")

        return handler

    async def _status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        state = self._hvac_state or "UNKNOWN"
        await update.message.reply_text(f"HVAC state: {state}")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    service = TelegramBotService(home_catalog_url=get_home_catalog_url())
    asyncio.run(service.start())


if __name__ == "__main__":
    main()
