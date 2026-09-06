from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Базовая модель ответов бэкенда: поля в JSON — camelCase, в Python — snake_case."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")


class UserDto(ApiModel):
    id: str
    name: str
    email: str | None = None
    telegram_id: str | None = None


class AuthResult(ApiModel):
    user: UserDto
    access_token: str
