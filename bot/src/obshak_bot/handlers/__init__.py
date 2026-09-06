from aiogram import Router

from obshak_bot.handlers import errors, group_chat, groups_private, start


def build_root_router() -> Router:
    root = Router(name="root")
    root.include_routers(errors.router, group_chat.router, start.router, groups_private.router)
    return root
