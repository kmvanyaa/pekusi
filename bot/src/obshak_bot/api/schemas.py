"""Модели данных бэкенда «Общака».

Соответствуют ответам их REST API (Express + Sequelize): поля в JSON — camelCase,
вложенные Sequelize-модели приходят под именем модели (`User`, `Category`, `ExpenseSplits`).
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")


# --- пользователи и auth ---


class UserDto(ApiModel):
    id: str
    name: str
    email: str | None = None
    telegram_id: str | None = None


class AuthResult(ApiModel):
    user: UserDto
    access_token: str


class MemberUserDto(ApiModel):
    id: str
    name: str


# --- группы ---


class GroupDto(ApiModel):
    id: str
    name: str
    currency: str = "RUB"
    invite_code: str
    owner_id: str


class GroupMemberDto(ApiModel):
    user_id: str
    role: str
    user: MemberUserDto = Field(alias="User")


# --- категории ---


class CategoryDto(ApiModel):
    id: str
    name: str
    icon: str | None = None
    color: str | None = None
    is_default: bool = False
    group_id: str | None = None


# --- расходы ---


class SplitInput(ApiModel):
    user_id: str
    amount_owed: Decimal


class ExpenseCreate(ApiModel):
    group_id: str
    payer_id: str
    category_id: str
    amount: Decimal
    description: str | None = None
    date: datetime | None = None
    splits: list[SplitInput] | None = None


class ExpenseUpdate(ApiModel):
    amount: Decimal | None = None
    description: str | None = None
    category_id: str | None = None
    date: datetime | None = None


class ExpenseSplitDto(ApiModel):
    user_id: str
    amount_owed: Decimal
    is_paid: bool = False
    user: MemberUserDto | None = Field(default=None, alias="User")


class ExpenseDto(ApiModel):
    id: str
    group_id: str
    payer_id: str
    category_id: str | None = None
    amount: Decimal
    description: str | None = None
    date: datetime
    payer: MemberUserDto | None = None
    category: CategoryDto | None = Field(default=None, alias="Category")
    splits: list[ExpenseSplitDto] = Field(default_factory=list, alias="ExpenseSplits")


class RecognizedReceiptDto(ApiModel):
    amount: Decimal | None = None
    date: datetime | None = None
    category: str | None = None
    description: str | None = None


# --- долги ---


class DebtDto(ApiModel):
    from_user_id: str
    to_user_id: str
    amount: Decimal
    group_id: str | None = None


# --- копилки ---


class ContributionDto(ApiModel):
    id: str
    user_id: str
    amount: Decimal
    note: str | None = None
    created_at: datetime
    user: MemberUserDto | None = Field(default=None, alias="User")


class SavingsGoalDto(ApiModel):
    id: str
    group_id: str
    name: str
    type: str = "group"
    target_amount: Decimal
    current_amount: Decimal = Decimal(0)
    created_by: str
    deadline: datetime | None = None
    status: str = "active"
    contributions: list[ContributionDto] = Field(default_factory=list, alias="Contributions")


# --- аналитика ---


class MonthlySummaryDto(ApiModel):
    total: Decimal
    by_category: dict[str, Decimal]
    by_payer: dict[str, Decimal]


class BudgetPredictionDto(ApiModel):
    total_spent: Decimal
    projected_total: Decimal
    daily_avg: Decimal
