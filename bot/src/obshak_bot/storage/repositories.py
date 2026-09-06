from dataclasses import dataclass

from obshak_bot.storage.db import Database


@dataclass(frozen=True, slots=True)
class UserSession:
    telegram_id: int
    user_id: str
    access_token: str
    current_group_id: str | None


class UserSessionRepository:
    """Кэш входа пользователя в бэкенд и его текущая группа."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def get(self, telegram_id: int) -> UserSession | None:
        cursor = await self._db.conn.execute(
            "SELECT telegram_id, user_id, access_token, current_group_id "
            "FROM user_sessions WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = await cursor.fetchone()
        return UserSession(**row) if row else None

    async def save_login(self, telegram_id: int, user_id: str, access_token: str) -> None:
        """Сохранить результат входа. Текущая группа при повторном входе сохраняется."""
        await self._db.conn.execute(
            "INSERT INTO user_sessions (telegram_id, user_id, access_token) VALUES (?, ?, ?) "
            "ON CONFLICT(telegram_id) DO UPDATE SET "
            "user_id = excluded.user_id, access_token = excluded.access_token, "
            "updated_at = datetime('now')",
            (telegram_id, user_id, access_token),
        )
        await self._db.conn.commit()

    async def set_current_group(self, telegram_id: int, group_id: str | None) -> None:
        await self._db.conn.execute(
            "UPDATE user_sessions SET current_group_id = ? WHERE telegram_id = ?",
            (group_id, telegram_id),
        )
        await self._db.conn.commit()

    async def delete(self, telegram_id: int) -> None:
        await self._db.conn.execute(
            "DELETE FROM user_sessions WHERE telegram_id = ?", (telegram_id,)
        )
        await self._db.conn.commit()


class ChatGroupRepository:
    """Привязка Telegram-чата к группе «Общака»."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def get_group_id(self, chat_id: int) -> str | None:
        cursor = await self._db.conn.execute(
            "SELECT group_id FROM chat_groups WHERE chat_id = ?", (chat_id,)
        )
        row = await cursor.fetchone()
        return row["group_id"] if row else None

    async def bind(self, chat_id: int, group_id: str) -> None:
        await self._db.conn.execute(
            "INSERT INTO chat_groups (chat_id, group_id) VALUES (?, ?) "
            "ON CONFLICT(chat_id) DO UPDATE SET group_id = excluded.group_id, "
            "bound_at = datetime('now')",
            (chat_id, group_id),
        )
        await self._db.conn.commit()

    async def unbind(self, chat_id: int) -> None:
        await self._db.conn.execute("DELETE FROM chat_groups WHERE chat_id = ?", (chat_id,))
        await self._db.conn.commit()


class ProcessedUpdateRepository:
    """Идемпотентность: какие update_id от Telegram уже обработаны."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def try_mark(self, update_id: int) -> bool:
        """Пометить update обработанным. False — если он уже был обработан раньше."""
        cursor = await self._db.conn.execute(
            "INSERT OR IGNORE INTO processed_updates (update_id) VALUES (?)", (update_id,)
        )
        await self._db.conn.commit()
        return cursor.rowcount == 1

    async def purge_older_than(self, days: int) -> int:
        cursor = await self._db.conn.execute(
            "DELETE FROM processed_updates WHERE processed_at < datetime('now', ?)",
            (f"-{days} days",),
        )
        await self._db.conn.commit()
        return cursor.rowcount
