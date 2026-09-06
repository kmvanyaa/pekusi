from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from obshak_bot.api import GroupDto

BTN_GROUPS = "👥 Группы"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=BTN_GROUPS)]], resize_keyboard=True)


class GroupCb(CallbackData, prefix="grp"):
    action: str  # select | members | invite | create | join | back
    group_id: str = ""


def groups_menu(groups: list[GroupDto], current_group_id: str | None) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=("✅ " if group.id == current_group_id else "") + group.name,
                callback_data=GroupCb(action="select", group_id=group.id).pack(),
            )
        ]
        for group in groups
    ]
    rows.append(
        [
            InlineKeyboardButton(text="➕ Создать", callback_data=GroupCb(action="create").pack()),
            InlineKeyboardButton(
                text="🔑 Вступить по коду", callback_data=GroupCb(action="join").pack()
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def group_card(group: GroupDto) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Участники",
                    callback_data=GroupCb(action="members", group_id=group.id).pack(),
                ),
                InlineKeyboardButton(
                    text="🔗 Пригласить",
                    callback_data=GroupCb(action="invite", group_id=group.id).pack(),
                ),
            ],
            [InlineKeyboardButton(text="⬅️ К списку", callback_data=GroupCb(action="back").pack())],
        ]
    )
