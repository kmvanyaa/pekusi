"""Мини-заглушка бэкенда «Общака» для тестов сервисов (поверх httpx.MockTransport)."""

import json
from itertools import count

import httpx

from obshak_bot.api import ObshakApiClient


class FakeBackend:
    def __init__(self) -> None:
        self.users: dict[str, dict] = {}  # telegramId -> user
        self.groups: dict[str, dict] = {}  # groupId -> group
        self.members: dict[str, set[str]] = {}  # groupId -> userIds
        self.valid_tokens: set[str] = set()
        self.calls: list[str] = []
        self._ids = count(1)

    def add_user(self, telegram_id: int, name: str) -> str:
        user_id = f"u{next(self._ids)}"
        self.users[str(telegram_id)] = {"id": user_id, "name": name, "telegramId": str(telegram_id)}
        return user_id

    def revoke_all_tokens(self) -> None:
        self.valid_tokens.clear()

    def client(self) -> ObshakApiClient:
        return ObshakApiClient(
            "http://backend.test", timeout_seconds=1, transport=httpx.MockTransport(self._handle)
        )

    # --- routing ---

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(f"{request.method} {request.url.path}")
        path = request.url.path
        body = json.loads(request.content) if request.content else {}

        if path == "/api/auth/telegram":
            user = self.users.get(body["telegramId"])
            if user is None:
                return httpx.Response(404, json={"message": "Пользователь не найден"})
            token = f"token-{user['id']}-{next(self._ids)}"
            self.valid_tokens.add(token)
            return httpx.Response(200, json={"user": user, "accessToken": token})

        user_id = self._authorize(request)
        if user_id is None:
            return httpx.Response(401, json={"message": "Недействительный токен"})

        if path == "/api/groups" and request.method == "POST":
            group_id = f"g{next(self._ids)}"
            group = {
                "id": group_id,
                "name": body["name"],
                "currency": "RUB",
                "inviteCode": f"CODE{group_id.upper()}",
                "ownerId": user_id,
            }
            self.groups[group_id] = group
            self.members[group_id] = {user_id}
            return httpx.Response(201, json=group)

        if path == "/api/groups/my":
            mine = [g for gid, g in self.groups.items() if user_id in self.members[gid]]
            return httpx.Response(200, json=mine)

        if path == "/api/groups/join":
            group = next(
                (g for g in self.groups.values() if g["inviteCode"] == body["inviteCode"]), None
            )
            if group is None:
                return httpx.Response(404, json={"message": "Группа не найдена"})
            if user_id in self.members[group["id"]]:
                return httpx.Response(400, json={"message": "Вы уже состоите в этой группе"})
            self.members[group["id"]].add(user_id)
            return httpx.Response(200, json={"message": "ok", "groupId": group["id"]})

        if path.startswith("/api/groups/") and path.endswith("/members"):
            group_id = path.split("/")[3]
            users_by_id = {u["id"]: u for u in self.users.values()}
            rows = [
                {
                    "userId": uid,
                    "role": "owner" if self.groups[group_id]["ownerId"] == uid else "member",
                    "User": {"id": uid, "name": users_by_id[uid]["name"]},
                }
                for uid in self.members[group_id]
            ]
            return httpx.Response(200, json=rows)

        return httpx.Response(404, json={"message": f"no route {path}"})

    def _authorize(self, request: httpx.Request) -> str | None:
        auth = request.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip()
        if token not in self.valid_tokens:
            return None
        return token.split("-")[1]
