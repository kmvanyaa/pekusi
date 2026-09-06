from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from obshak_bot.api import ApiError, ApiNotFound, ApiUnavailable, ObshakApiClient

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, api: ObshakApiClient) -> None:
    if message.from_user is None:
        return

    try:
        auth = await api.login_by_telegram(message.from_user.id)
    except ApiNotFound:
        await message.answer(
            "Я тебя ещё не знаю.\n"
            f"Твой Telegram ID: <code>{message.from_user.id}</code> — "
            "укажи его в профиле на сайте «Общак» и нажми /start снова."
        )
        return
    except ApiUnavailable:
        await message.answer("Сервер «Общака» сейчас недоступен. Попробуй через минуту.")
        return
    except ApiError as exc:
        await message.answer(f"Не получилось войти: {exc.message}")
        return

    await message.answer(f"Привет, {auth.user.name}! Ты в «Общаке». Скоро здесь появится меню.")
