import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from obshak_bot.api import ObshakApiClient
from obshak_bot.config import Settings
from obshak_bot.handlers import build_root_router

log = logging.getLogger("obshak_bot")


async def run() -> None:
    settings = Settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    bot = Bot(
        settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    api = ObshakApiClient(str(settings.backend_url), settings.backend_timeout_seconds)

    dispatcher = Dispatcher()
    dispatcher["api"] = api
    dispatcher.include_router(build_root_router())

    try:
        me = await bot.get_me()
        log.info("Started as @%s, backend=%s", me.username, settings.backend_url)
        # Не отвечать пачкой на сообщения, накопившиеся пока бот был выключен.
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)
    finally:
        await api.aclose()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(run())
