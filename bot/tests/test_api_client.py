import httpx
import pytest

from obshak_bot.api import ApiError, ApiNotFound, ApiUnavailable, ObshakApiClient


def make_client(handler) -> ObshakApiClient:
    return ObshakApiClient(
        "http://backend.test",
        timeout_seconds=1,
        transport=httpx.MockTransport(handler),
    )


async def test_login_by_telegram_returns_user_and_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/auth/telegram"
        assert request.content == b'{"telegramId":"42"}'
        return httpx.Response(
            200,
            json={
                "user": {"id": "u1", "email": "a@b.c", "name": "Артём", "telegramId": "42"},
                "accessToken": "jwt",
            },
        )

    client = make_client(handler)
    result = await client.login_by_telegram(42)

    assert result.access_token == "jwt"
    assert result.user.id == "u1"
    assert result.user.telegram_id == "42"


async def test_404_raises_not_found_with_backend_message() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Пользователь не найден"})

    with pytest.raises(ApiNotFound) as exc_info:
        await make_client(handler).login_by_telegram(1)
    assert exc_info.value.message == "Пользователь не найден"


async def test_other_errors_raise_api_error_with_status() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    with pytest.raises(ApiError) as exc_info:
        await make_client(handler).login_by_telegram(1)
    assert exc_info.value.status_code == 500


async def test_network_failure_raises_unavailable() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(ApiUnavailable):
        await make_client(handler).login_by_telegram(1)
