from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from obshak_bot.api import ApiError, ApiNotFound, ApiUnavailable
from obshak_bot.services import AuthService

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, auth: AuthService) -> None:
    if message.from_user is None:
        return

    try:
        user, session = await auth.login(message.from_user.id)
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

    group_hint = (
        "Текущая группа выбрана." if session.current_group_id else "Группа пока не выбрана."
    )
    await message.answer(f"Привет, {user.name}! Ты в «Общаке». {group_hint}")
