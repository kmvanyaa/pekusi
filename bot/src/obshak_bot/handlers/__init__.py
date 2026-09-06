from aiogram import Router

from obshak_bot.handlers import start


def build_root_router() -> Router:
    root = Router(name="root")
    root.include_router(start.router)
    return root
