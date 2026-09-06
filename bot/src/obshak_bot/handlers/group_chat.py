from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import (
    JOIN_TRANSITION,
    LEAVE_TRANSITION,
    ChatMemberUpdatedFilter,
    Command,
    CommandStart,
)
from aiogram.types import ChatMemberUpdated, Message

from obshak_bot.services import GroupService

router = Router(name="group_chat")
_GROUP_TYPES = {ChatType.GROUP, ChatType.SUPERGROUP}
router.message.filter(F.chat.type.in_(_GROUP_TYPES))
router.my_chat_member.filter(F.chat.type.in_(_GROUP_TYPES))


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def bot_added(event: ChatMemberUpdated, groups: GroupService) -> None:
    await _bind_or_report(
        event.chat.id, event.chat.title or "Общая группа", event.from_user.id, event, groups
    )


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION))
async def bot_removed(event: ChatMemberUpdated, groups: GroupService) -> None:
    await groups.unbind_chat(event.chat.id)


@router.message(CommandStart())
@router.message(Command("join"))
async def join_chat_group(message: Message, groups: GroupService) -> None:
    if message.from_user is None:
        return
    binding = await groups.chat_binding(message.chat.id)
    if binding is None:
        await _bind_or_report(
            message.chat.id,
            message.chat.title or "Общая группа",
            message.from_user.id,
            message,
            groups,
        )
        return
    joined = await groups.join_chat_group(message.from_user.id, binding)
    if joined:
        await message.answer(f"{message.from_user.full_name} теперь в группе.")
    else:
        await message.answer(f"{message.from_user.full_name}, ты уже в группе.")


async def _bind_or_report(
    chat_id: int,
    title: str,
    owner_telegram_id: int,
    event: ChatMemberUpdated | Message,
    groups: GroupService,
) -> None:
    group = await groups.bind_chat(chat_id, owner_telegram_id, title)
    await event.answer(
        f"Чат привязан к группе «{group.name}» в «Общаке».\n"
        "Все, кто напишет в чат или нажмёт /join, автоматически станут её участниками."
    )
