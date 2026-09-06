import logging
from datetime import date
from decimal import Decimal
from typing import Any

import httpx
from pydantic import BaseModel

from obshak_bot.api.schemas import (
    AuthResult,
    BudgetPredictionDto,
    CategoryDto,
    DebtDto,
    ExpenseCreate,
    ExpenseDto,
    ExpenseUpdate,
    GroupDto,
    GroupMemberDto,
    MonthlySummaryDto,
    RecognizedReceiptDto,
    SavingsGoalDto,
)

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


class ApiUnauthorized(ApiError):
    """Токен недействителен или истёк (401)."""

    def __init__(self, message: str) -> None:
        super().__init__(401, message)


class ApiUnavailable(Exception):
    """Не удалось связаться с бэкендом (сеть, таймаут)."""


class ObshakApiClient:
    """HTTP-клиент к веб-бэкенду «Общака». Единственная точка доступа бота к данным."""

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

    # --- auth ---

    async def login_by_telegram(self, telegram_id: int) -> AuthResult:
        """Вход пользователя по Telegram ID. Бросает ApiNotFound, если бэкенд его не знает."""
        data = await self._request(
            "POST", "/api/auth/telegram", json={"telegramId": str(telegram_id)}
        )
        return AuthResult.model_validate(data)

    # --- groups ---

    async def create_group(self, token: str, name: str) -> GroupDto:
        data = await self._request("POST", "/api/groups", token=token, json={"name": name})
        return GroupDto.model_validate(data)

    async def my_groups(self, token: str) -> list[GroupDto]:
        data = await self._request("GET", "/api/groups/my", token=token)
        return [GroupDto.model_validate(item) for item in data]

    async def join_group(self, token: str, invite_code: str) -> str:
        """Вступить в группу по коду. Возвращает id группы."""
        data = await self._request(
            "POST", "/api/groups/join", token=token, json={"inviteCode": invite_code}
        )
        return data["groupId"]

    async def group_members(self, token: str, group_id: str) -> list[GroupMemberDto]:
        data = await self._request("GET", f"/api/groups/{group_id}/members", token=token)
        return [GroupMemberDto.model_validate(item) for item in data]

    # --- categories ---

    async def categories(self, token: str, group_id: str | None = None) -> list[CategoryDto]:
        """Общие категории + категории группы (если указана)."""
        params = {"groupId": group_id} if group_id else None
        data = await self._request("GET", "/api/categories", token=token, params=params)
        return [CategoryDto.model_validate(item) for item in data]

    async def create_category(
        self, token: str, name: str, group_id: str | None = None, icon: str | None = None
    ) -> CategoryDto:
        payload = _compact({"name": name, "groupId": group_id, "icon": icon})
        data = await self._request("POST", "/api/categories", token=token, json=payload)
        return CategoryDto.model_validate(data)

    # --- expenses ---

    async def create_expense(self, token: str, expense: ExpenseCreate) -> ExpenseDto:
        data = await self._request(
            "POST", "/api/expenses", token=token, json=_json_payload(expense)
        )
        return ExpenseDto.model_validate(data)

    async def expenses(
        self,
        token: str,
        group_id: str,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        category_id: str | None = None,
        user_id: str | None = None,
    ) -> list[ExpenseDto]:
        params = _compact(
            {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
                "categoryId": category_id,
                "userId": user_id,
            }
        )
        data = await self._request(
            "GET", f"/api/expenses/group/{group_id}", token=token, params=params
        )
        return [ExpenseDto.model_validate(item) for item in data]

    async def update_expense(
        self, token: str, expense_id: str, changes: ExpenseUpdate
    ) -> ExpenseDto:
        data = await self._request(
            "PUT", f"/api/expenses/{expense_id}", token=token, json=_json_payload(changes)
        )
        return ExpenseDto.model_validate(data)

    async def delete_expense(self, token: str, expense_id: str) -> None:
        await self._request("DELETE", f"/api/expenses/{expense_id}", token=token)

    async def recognize_receipt(self, token: str, image: bytes) -> RecognizedReceiptDto:
        """Распознавание чека на бэкенде (у них пока заглушка)."""
        data = await self._request(
            "POST",
            "/api/expenses/receipt",
            token=token,
            files={"photo": ("receipt.jpg", image, "image/jpeg")},
        )
        return RecognizedReceiptDto.model_validate(data)

    # --- debts ---

    async def my_debts(self, token: str) -> list[DebtDto]:
        data = await self._request("GET", "/api/debts/my", token=token)
        return [DebtDto.model_validate(item) for item in data]

    async def group_debts(self, token: str, group_id: str) -> list[DebtDto]:
        data = await self._request("GET", f"/api/debts/group/{group_id}", token=token)
        return [DebtDto.model_validate(item) for item in data]

    async def pay_debt(self, token: str, debt_id: str, amount: Decimal) -> None:
        """Зафиксировать возврат долга. На бэкенде пока не реализовано (501)."""
        await self._request(
            "POST", f"/api/debts/{debt_id}/pay", token=token, json={"amount": float(amount)}
        )

    # --- savings goals ---

    async def savings_goals(self, token: str, group_id: str) -> list[SavingsGoalDto]:
        data = await self._request("GET", f"/api/savings-goals/group/{group_id}", token=token)
        return [SavingsGoalDto.model_validate(item) for item in data]

    async def create_savings_goal(
        self,
        token: str,
        group_id: str,
        name: str,
        target_amount: Decimal,
        goal_type: str = "group",
    ) -> SavingsGoalDto:
        payload = {
            "groupId": group_id,
            "name": name,
            "type": goal_type,
            "targetAmount": float(target_amount),
        }
        data = await self._request("POST", "/api/savings-goals", token=token, json=payload)
        return SavingsGoalDto.model_validate(data)

    async def contribute(
        self, token: str, goal_id: str, amount: Decimal, note: str | None = None
    ) -> SavingsGoalDto:
        payload = _compact({"amount": float(amount), "note": note})
        data = await self._request(
            "POST", f"/api/savings-goals/{goal_id}/contribute", token=token, json=payload
        )
        return SavingsGoalDto.model_validate(data)

    # --- analytics ---

    async def monthly_summary(
        self, token: str, group_id: str, month: str | None = None
    ) -> MonthlySummaryDto:
        """Итоги месяца (`month` в формате YYYY-MM, по умолчанию текущий)."""
        params = {"month": month} if month else None
        data = await self._request(
            "GET", f"/api/analytics/group/{group_id}/summary", token=token, params=params
        )
        return MonthlySummaryDto.model_validate(data)

    async def budget_prediction(self, token: str, group_id: str) -> BudgetPredictionDto:
        data = await self._request(
            "GET", f"/api/analytics/group/{group_id}/prediction", token=token
        )
        return BudgetPredictionDto.model_validate(data)

    # --- internals ---

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
        if response.status_code == 401:
            raise ApiUnauthorized(message)
        raise ApiError(response.status_code, message)


def _json_payload(model: BaseModel) -> dict[str, Any]:
    """Тело запроса для бэкенда: camelCase, без None, Decimal -> число (zod ждёт number)."""
    return _to_json_numbers(model.model_dump(by_alias=True, exclude_none=True))


def _to_json_numbers(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: _to_json_numbers(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_json_numbers(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _compact(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


def _error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.reason_phrase
    if isinstance(body, dict) and isinstance(body.get("message"), str):
        return body["message"]
    return response.reason_phrase
