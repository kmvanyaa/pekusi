import logging
from typing import Any

import httpx

from obshak_bot.api.schemas import AuthResult

log = logging.getLogger(__name__)


class ApiError(Exception):
    """Бэкенд ответил ошибкой (4xx/5xx)."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"{status_code}: {message}")
        self.status_code = status_code
        self.message = message


class ApiNotFound(ApiError):
    """Ресурс не найден (404)."""

    def __init__(self, message: str) -> None:
        super().__init__(404, message)


class ApiUnavailable(Exception):
    """Не удалось связаться с бэкендом (сеть, таймаут)."""


class ObshakApiClient:
    """HTTP-клиент к веб-бэкенду «Общака»."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout_seconds,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def login_by_telegram(self, telegram_id: int) -> AuthResult:
        """Вход пользователя по Telegram ID. Бросает ApiNotFound, если бэкенд его не знает."""
        data = await self._request(
            "POST", "/api/auth/telegram", json={"telegramId": str(telegram_id)}
        )
        return AuthResult.model_validate(data)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        **kwargs: Any,
    ) -> Any:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            response = await self._http.request(method, path, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            log.warning("Backend unreachable: %s %s (%s)", method, path, type(exc).__name__)
            raise ApiUnavailable(str(exc)) from exc

        if response.is_success:
            return response.json() if response.content else None

        message = _error_message(response)
        log.info("Backend error: %s %s -> %s %s", method, path, response.status_code, message)
        if response.status_code == 404:
            raise ApiNotFound(message)
        raise ApiError(response.status_code, message)


def _error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.reason_phrase
    if isinstance(body, dict) and isinstance(body.get("message"), str):
        return body["message"]
    return response.reason_phrase
