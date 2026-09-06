from collections.abc import Awaitable, Callable

from obshak_bot.api import ApiNotFound, ApiUnauthorized, ObshakApiClient, UserDto
from obshak_bot.storage import UserSession, UserSessionRepository


class UserNotRegistered(Exception):
    """Бэкенд не знает пользователя с таким Telegram ID."""

    def __init__(self, telegram_id: int) -> None:
        super().__init__(f"Telegram user {telegram_id} is not registered")
        self.telegram_id = telegram_id


class AuthService:
    """Вход пользователя Telegram в бэкенд и кэширование его сессии."""

    def __init__(self, api: ObshakApiClient, sessions: UserSessionRepository) -> None:
        self._api = api
        self._sessions = sessions

    async def login(self, telegram_id: int) -> tuple[UserDto, UserSession]:
        """Войти через бэкенд и сохранить токен."""
        try:
            auth = await self._api.login_by_telegram(telegram_id)
        except ApiNotFound as exc:
            raise UserNotRegistered(telegram_id) from exc
        await self._sessions.save_login(telegram_id, auth.user.id, auth.access_token)
        session = await self._sessions.get(telegram_id)
        assert session is not None
        return auth.user, session

    async def ensure_session(self, telegram_id: int) -> UserSession:
        """Вернуть кэшированную сессию или войти заново."""
        session = await self._sessions.get(telegram_id)
        if session is None:
            _, session = await self.login(telegram_id)
        return session

    async def run_authorized[T](
        self, telegram_id: int, operation: Callable[[str], Awaitable[T]]
    ) -> T:
        """Выполнить запрос с токеном пользователя; при 401 — перелогиниться и повторить."""
        session = await self.ensure_session(telegram_id)
        try:
            return await operation(session.access_token)
        except ApiUnauthorized:
            _, session = await self.login(telegram_id)
            return await operation(session.access_token)
