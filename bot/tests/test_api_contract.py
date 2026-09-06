"""Контракт клиента с REST API бэкенда: пути, форма тела запроса, разбор ответов."""

import json
from datetime import date, datetime
from decimal import Decimal

import httpx

from obshak_bot.api import ExpenseCreate, ExpenseUpdate, ObshakApiClient, SplitInput


class Recorder:
    """MockTransport, который запоминает запрос и отдаёт заданный ответ."""

    def __init__(self, status: int, body) -> None:
        self.status = status
        self.body = body
        self.request: httpx.Request | None = None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.request = request
        return httpx.Response(self.status, json=self.body)

    @property
    def json(self):
        assert self.request is not None
        return json.loads(self.request.content)


def make_client(recorder: Recorder) -> ObshakApiClient:
    return ObshakApiClient(
        "http://backend.test", timeout_seconds=1, transport=httpx.MockTransport(recorder)
    )


async def test_categories_query_and_parse() -> None:
    rec = Recorder(
        200,
        [
            {
                "id": "c1",
                "name": "Продукты",
                "icon": "🛒",
                "color": None,
                "isDefault": True,
                "groupId": None,
            },
            {"id": "c2", "name": "Кино", "isDefault": False, "groupId": "g1"},
        ],
    )
    result = await make_client(rec).categories("t", group_id="g1")

    assert rec.request.url.path == "/api/categories"
    assert rec.request.url.params["groupId"] == "g1"
    assert rec.request.headers["Authorization"] == "Bearer t"
    assert [(c.name, c.is_default) for c in result] == [("Продукты", True), ("Кино", False)]


async def test_create_expense_sends_camel_case_numbers_and_splits() -> None:
    rec = Recorder(
        201,
        {
            "id": "e1",
            "groupId": "g1",
            "payerId": "u1",
            "categoryId": "c1",
            "amount": "100.00",
            "date": "2026-09-06T10:00:00.000Z",
        },
    )
    expense = ExpenseCreate(
        group_id="g1",
        payer_id="u1",
        category_id="c1",
        amount=Decimal("100.00"),
        description="Пицца",
        splits=[
            SplitInput(user_id="u1", amount_owed=Decimal("34")),
            SplitInput(user_id="u2", amount_owed=Decimal("33")),
            SplitInput(user_id="u3", amount_owed=Decimal("33")),
        ],
    )

    created = await make_client(rec).create_expense("t", expense)

    assert rec.request.url.path == "/api/expenses"
    assert rec.json == {
        "groupId": "g1",
        "payerId": "u1",
        "categoryId": "c1",
        "amount": 100.0,
        "description": "Пицца",
        "splits": [
            {"userId": "u1", "amountOwed": 34.0},
            {"userId": "u2", "amountOwed": 33.0},
            {"userId": "u3", "amountOwed": 33.0},
        ],
    }
    assert created.id == "e1" and created.amount == Decimal("100.00")


async def test_expenses_filters_and_nested_sequelize_includes() -> None:
    rec = Recorder(
        200,
        [
            {
                "id": "e1",
                "groupId": "g1",
                "payerId": "u1",
                "categoryId": "c1",
                "amount": "300.00",
                "description": None,
                "date": "2026-09-06T10:00:00.000Z",
                "payer": {"id": "u1", "name": "Артём"},
                "Category": {"id": "c1", "name": "Продукты", "icon": "🛒", "color": "#fff"},
                "ExpenseSplits": [
                    {
                        "userId": "u1",
                        "amountOwed": "150.00",
                        "isPaid": True,
                        "User": {"id": "u1", "name": "Артём"},
                    },
                    {
                        "userId": "u2",
                        "amountOwed": "150.00",
                        "isPaid": False,
                        "User": {"id": "u2", "name": "Друг"},
                    },
                ],
            }
        ],
    )
    result = await make_client(rec).expenses(
        "t", "g1", date_from=date(2026, 9, 1), date_to=date(2026, 9, 30), category_id="c1"
    )

    assert rec.request.url.path == "/api/expenses/group/g1"
    assert dict(rec.request.url.params) == {
        "from": "2026-09-01",
        "to": "2026-09-30",
        "categoryId": "c1",
    }
    expense = result[0]
    assert expense.payer.name == "Артём"
    assert expense.category.name == "Продукты"
    assert [(s.user.name, s.amount_owed, s.is_paid) for s in expense.splits] == [
        ("Артём", Decimal("150.00"), True),
        ("Друг", Decimal("150.00"), False),
    ]
    assert expense.date == datetime.fromisoformat("2026-09-06T10:00:00+00:00")


async def test_update_expense_sends_only_changed_fields() -> None:
    rec = Recorder(
        200,
        {
            "id": "e1",
            "groupId": "g1",
            "payerId": "u1",
            "amount": "50",
            "date": "2026-09-06T10:00:00.000Z",
        },
    )
    await make_client(rec).update_expense("t", "e1", ExpenseUpdate(amount=Decimal("50")))

    assert rec.request.method == "PUT"
    assert rec.request.url.path == "/api/expenses/e1"
    assert rec.json == {"amount": 50.0}


async def test_delete_expense() -> None:
    rec = Recorder(200, {"message": "Расход удалён"})
    await make_client(rec).delete_expense("t", "e1")
    assert (rec.request.method, rec.request.url.path) == ("DELETE", "/api/expenses/e1")


async def test_recognize_receipt_uploads_photo_field() -> None:
    rec = Recorder(
        200,
        {
            "amount": 1234.56,
            "date": "2026-09-06T10:00:00.000Z",
            "category": "Продукты",
            "description": "Магазин",
        },
    )
    result = await make_client(rec).recognize_receipt("t", b"\xff\xd8jpeg")

    assert rec.request.url.path == "/api/expenses/receipt"
    assert b'name="photo"' in rec.request.content
    assert result.amount == Decimal("1234.56")


async def test_my_debts_parse() -> None:
    rec = Recorder(200, [{"fromUserId": "u2", "toUserId": "u1", "amount": 150, "groupId": "g1"}])
    debts = await make_client(rec).my_debts("t")

    assert rec.request.url.path == "/api/debts/my"
    assert (debts[0].from_user_id, debts[0].to_user_id, debts[0].amount) == (
        "u2",
        "u1",
        Decimal(150),
    )


async def test_savings_goal_create_contribute_and_list() -> None:
    goal_json = {
        "id": "s1",
        "groupId": "g1",
        "name": "Отпуск",
        "type": "group",
        "targetAmount": "10000.00",
        "currentAmount": "500.00",
        "createdBy": "u1",
        "deadline": None,
        "status": "active",
    }
    rec = Recorder(201, goal_json)
    client = make_client(rec)
    goal = await client.create_savings_goal("t", "g1", "Отпуск", Decimal("10000"))
    assert rec.json == {"groupId": "g1", "name": "Отпуск", "type": "group", "targetAmount": 10000.0}
    assert goal.target_amount == Decimal("10000.00")

    rec = Recorder(200, goal_json)
    await make_client(rec).contribute("t", "s1", Decimal("500"), note="аванс")
    assert rec.request.url.path == "/api/savings-goals/s1/contribute"
    assert rec.json == {"amount": 500.0, "note": "аванс"}

    rec = Recorder(
        200,
        [
            {
                **goal_json,
                "Contributions": [
                    {
                        "id": "k1",
                        "userId": "u1",
                        "amount": "500.00",
                        "note": None,
                        "createdAt": "2026-09-06T10:00:00.000Z",
                        "User": {"id": "u1", "name": "Артём"},
                    }
                ],
            }
        ],
    )
    goals = await make_client(rec).savings_goals("t", "g1")
    assert rec.request.url.path == "/api/savings-goals/group/g1"
    assert goals[0].contributions[0].user.name == "Артём"
    assert goals[0].contributions[0].amount == Decimal("500.00")


async def test_analytics_summary_and_prediction() -> None:
    rec = Recorder(
        200,
        {"total": 1500, "byCategory": {"Продукты": 1000, "Кино": 500}, "byPayer": {"Артём": 1500}},
    )
    summary = await make_client(rec).monthly_summary("t", "g1", month="2026-09")
    assert rec.request.url.path == "/api/analytics/group/g1/summary"
    assert rec.request.url.params["month"] == "2026-09"
    assert summary.by_category["Кино"] == Decimal(500)

    rec = Recorder(200, {"totalSpent": 1500, "projectedTotal": 7500, "dailyAvg": 250})
    prediction = await make_client(rec).budget_prediction("t", "g1")
    assert prediction.projected_total == Decimal(7500)
