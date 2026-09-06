import httpx
import pytest

from obshak_bot.api import ApiNotFound, ObshakApiClient
from obshak_bot.services import AuthService
from obshak_bot.storage import Database, UserSessionRepository


def make_api(handler) -> ObshakApiClient:
    return ObshakApiClient(
        "http://backend.test", timeout_seconds=1, transport=httpx.MockTransport(handler)
    )


async def test_login_caches_session(db: Database) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"user": {"id": "u1", "name": "Артём"}, "accessToken": "jwt"}
        )

    sessions = UserSessionRepository(db)
    service = AuthService(make_api(handler), sessions)

    user, session = await service.login(42)

    assert user.name == "Артём"
    assert session.access_token == "jwt"
    assert await service.get_session(42) == session


async def test_login_failure_leaves_no_session(db: Database) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "нет"})

    service = AuthService(make_api(handler), UserSessionRepository(db))

    with pytest.raises(ApiNotFound):
        await service.login(42)
    assert await service.get_session(42) is None
