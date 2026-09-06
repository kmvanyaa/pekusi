from obshak_bot.api import ObshakApiClient, UserDto
from obshak_bot.storage import UserSession, UserSessionRepository


class AuthService:
    """Вход пользователя Telegram в бэкенд и кэширование его сессии."""

    def __init__(self, api: ObshakApiClient, sessions: UserSessionRepository) -> None:
        self._api = api
        self._sessions = sessions

    async def login(self, telegram_id: int) -> tuple[UserDto, UserSession]:
        """Войти через бэкенд и сохранить токен. Ошибки API пробрасываются вызывающему."""
        auth = await self._api.login_by_telegram(telegram_id)
        await self._sessions.save_login(telegram_id, auth.user.id, auth.access_token)
        session = await self._sessions.get(telegram_id)
        assert session is not None
        return auth.user, session

    async def get_session(self, telegram_id: int) -> UserSession | None:
        return await self._sessions.get(telegram_id)
