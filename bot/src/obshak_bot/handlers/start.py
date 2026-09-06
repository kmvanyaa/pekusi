from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from obshak_bot.keyboards import main_menu
from obshak_bot.services import AuthService, GroupService

router = Router(name="start")
router.message.filter(F.chat.type == ChatType.PRIVATE)

INVITE_PREFIX = "inv_"


@router.message(Command("cancel"), StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu())


@router.message(CommandStart(deep_link=True, magic=F.args.startswith(INVITE_PREFIX)))
async def cmd_start_with_invite(
    message: Message, command: CommandObject, auth: AuthService, groups: GroupService
) -> None:
    if message.from_user is None or command.args is None:
        return
    await auth.ensure_session(message.from_user.id)
    group = await groups.join_by_code(
        message.from_user.id, command.args.removeprefix(INVITE_PREFIX)
    )
    await message.answer(f"Ты вступил в группу «{group.name}».", reply_markup=main_menu())


@router.message(CommandStart())
async def cmd_start(message: Message, auth: AuthService, groups: GroupService) -> None:
    if message.from_user is None:
        return
    user, _ = await auth.login(message.from_user.id)
    current = await groups.current(message.from_user.id)
    group_hint = (
        f"Текущая группа: <b>{current.name}</b>."
        if current
        else "Группа пока не выбрана — открой «👥 Группы»."
    )
    await message.answer(f"Привет, {user.name}! {group_hint}", reply_markup=main_menu())
