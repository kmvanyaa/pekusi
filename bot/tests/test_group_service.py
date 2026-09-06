import pytest

from obshak_bot.api import ApiError
from obshak_bot.services import AuthService, GroupService
from obshak_bot.storage import ChatGroupRepository, Database, UserSessionRepository
from tests.fake_backend import FakeBackend


@pytest.fixture
def backend() -> FakeBackend:
    backend = FakeBackend()
    backend.add_user(1, "Owner")
    backend.add_user(2, "Friend")
    return backend


@pytest.fixture
def service(db: Database, backend: FakeBackend) -> GroupService:
    api = backend.client()
    sessions = UserSessionRepository(db)
    return GroupService(api, AuthService(api, sessions), sessions, ChatGroupRepository(db))


async def test_first_created_group_becomes_current(service: GroupService) -> None:
    first = await service.create(1, "Семья")
    second = await service.create(1, "Друзья")

    current = await service.current(1)
    assert current is not None and current.id == first.id
    assert {g.name for g in await service.list_my(1)} == {"Семья", "Друзья"}

    await service.select_current(1, second.id)
    assert (await service.current(1)).id == second.id


async def test_select_foreign_group_is_rejected(service: GroupService) -> None:
    group = await service.create(1, "Семья")
    with pytest.raises(ApiError):
        await service.select_current(2, group.id)


async def test_join_by_code_and_members(service: GroupService) -> None:
    group = await service.create(1, "Семья")

    joined = await service.join_by_code(2, group.invite_code)

    assert joined.id == group.id
    assert (await service.current(2)).id == group.id
    members = await service.members(1, group.id)
    assert {(m.user.name, m.role) for m in members} == {("Owner", "owner"), ("Friend", "member")}


async def test_bind_chat_and_auto_join(service: GroupService) -> None:
    group = await service.bind_chat(-100, owner_telegram_id=1, title="Квартира")
    binding = await service.chat_binding(-100)
    assert binding is not None and binding.group_id == group.id

    assert await service.join_chat_group(2, binding) is True  # вступил
    assert await service.join_chat_group(2, binding) is False  # уже в кэше
    assert await service.join_chat_group(1, binding) is False  # владелец

    names = {m.user.name for m in await service.members(1, group.id)}
    assert names == {"Owner", "Friend"}

    await service.unbind_chat(-100)
    assert await service.chat_binding(-100) is None


async def test_join_chat_group_when_backend_says_already_member(
    service: GroupService, backend: FakeBackend
) -> None:
    group = await service.bind_chat(-100, owner_telegram_id=1, title="Квартира")
    await service.join_by_code(2, group.invite_code)  # вступил вручную, кэш чата пуст

    binding = await service.chat_binding(-100)
    assert await service.join_chat_group(2, binding) is False
