import logging

from obshak_bot.api import ApiError, GroupDto, GroupMemberDto, ObshakApiClient
from obshak_bot.services.auth import AuthService
from obshak_bot.storage import ChatBinding, ChatGroupRepository, UserSessionRepository

log = logging.getLogger(__name__)


class GroupService:
    """Группы «Общака»: список, создание, вступление, текущая группа, привязка чатов."""

    def __init__(
        self,
        api: ObshakApiClient,
        auth: AuthService,
        sessions: UserSessionRepository,
        chats: ChatGroupRepository,
    ) -> None:
        self._api = api
        self._auth = auth
        self._sessions = sessions
        self._chats = chats

    # --- личный кабинет ---

    async def list_my(self, telegram_id: int) -> list[GroupDto]:
        return await self._auth.run_authorized(telegram_id, self._api.my_groups)

    async def current(self, telegram_id: int) -> GroupDto | None:
        session = await self._auth.ensure_session(telegram_id)
        if session.current_group_id is None:
            return None
        groups = await self.list_my(telegram_id)
        return next((g for g in groups if g.id == session.current_group_id), None)

    async def select_current(self, telegram_id: int, group_id: str) -> GroupDto:
        groups = await self.list_my(telegram_id)
        group = next((g for g in groups if g.id == group_id), None)
        if group is None:
            raise ApiError(403, "Ты не состоишь в этой группе")
        await self._sessions.set_current_group(telegram_id, group_id)
        return group

    async def create(self, telegram_id: int, name: str) -> GroupDto:
        group = await self._auth.run_authorized(
            telegram_id, lambda token: self._api.create_group(token, name)
        )
        await self._select_if_none(telegram_id, group.id)
        return group

    async def join_by_code(self, telegram_id: int, invite_code: str) -> GroupDto:
        group_id = await self._auth.run_authorized(
            telegram_id, lambda token: self._api.join_group(token, invite_code)
        )
        await self._select_if_none(telegram_id, group_id)
        groups = await self.list_my(telegram_id)
        return next(g for g in groups if g.id == group_id)

    async def members(self, telegram_id: int, group_id: str) -> list[GroupMemberDto]:
        return await self._auth.run_authorized(
            telegram_id, lambda token: self._api.group_members(token, group_id)
        )

    # --- групповые чаты Telegram ---

    async def chat_binding(self, chat_id: int) -> ChatBinding | None:
        return await self._chats.get(chat_id)

    async def bind_chat(self, chat_id: int, owner_telegram_id: int, title: str) -> GroupDto:
        """Создать группу «Общака» для Telegram-чата от имени пользователя и привязать чат."""
        group = await self.create(owner_telegram_id, title)
        await self._chats.bind(chat_id, group.id, group.invite_code)
        await self._chats.add_member(chat_id, owner_telegram_id)
        return group

    async def unbind_chat(self, chat_id: int) -> None:
        await self._chats.unbind(chat_id)

    async def join_chat_group(self, telegram_id: int, binding: ChatBinding) -> bool:
        """Вступить в группу чата. True — если пользователь только что вступил."""
        if await self._chats.is_member(binding.chat_id, telegram_id):
            return False
        try:
            await self.join_by_code(telegram_id, binding.invite_code)
            joined = True
        except ApiError as exc:
            if exc.status_code != 400:  # 400 — «уже состоишь в группе»
                raise
            joined = False
        await self._chats.add_member(binding.chat_id, telegram_id)
        return joined

    async def _select_if_none(self, telegram_id: int, group_id: str) -> None:
        session = await self._auth.ensure_session(telegram_id)
        if session.current_group_id is None:
            await self._sessions.set_current_group(telegram_id, group_id)
