-- Локальное состояние бота. Бизнес-данные («Общак») живут в бэкенде, здесь только то,
-- что нужно самому боту.

CREATE TABLE IF NOT EXISTS user_sessions (
    telegram_id      INTEGER PRIMARY KEY,
    user_id          TEXT    NOT NULL,
    access_token     TEXT    NOT NULL,
    current_group_id TEXT,
    updated_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat_groups (
    chat_id  INTEGER PRIMARY KEY,
    group_id TEXT    NOT NULL,
    bound_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS processed_updates (
    update_id    INTEGER PRIMARY KEY,
    processed_at TEXT NOT NULL DEFAULT (datetime('now'))
);
