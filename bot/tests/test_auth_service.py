import pytest

from obshak_bot.services import AuthService, UserNotRegistered
from obshak_bot.storage import Database, UserSessionRepository
from tests.fake_backend import FakeBackend


async def test_login_caches_session(db: Database) -> None:
    backend = FakeBackend()
    backend.add_user(42, "Артём")
    service = AuthService(backend.client(), UserSessionRepository(db))

    user, session = await service.login(42)

    assert user.name == "Артём"
    assert session.access_token in backend.valid_tokens
    assert await service.ensure_session(42) == session
    assert backend.calls.count("POST /api/auth/telegram") == 1


async def test_unknown_user_raises_not_registered(db: Database) -> None:
    service = AuthService(FakeBackend().client(), UserSessionRepository(db))

    with pytest.raises(UserNotRegistered) as exc_info:
        await service.ensure_session(42)
    assert exc_info.value.telegram_id == 42


async def test_run_authorized_relogins_on_401(db: Database) -> None:
    backend = FakeBackend()
    backend.add_user(42, "Артём")
    api = backend.client()
    service = AuthService(api, UserSessionRepository(db))
    await service.login(42)
    backend.revoke_all_tokens()

    groups = await service.run_authorized(42, api.my_groups)

    assert groups == []
    assert backend.calls.count("POST /api/auth/telegram") == 2
    assert backend.calls.count("GET /api/groups/my") == 2
