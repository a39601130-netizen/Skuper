"""API роутер: AI советник (PostgreSQL контекст)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_ai
from db.database import get_db
from db.services.finance import get_monthly_summary
from db.services.workout import get_workout_history
from services.ai_advisor import AIAdvisor

router = APIRouter(prefix="/api/advisor", tags=["advisor"])


class AskRequest(BaseModel):
    question: str
    mode: str = "default"
    context_type: str = "finance"


@router.post("/ask")
async def ask(
    data: AskRequest,
    user: dict = Depends(get_current_user),
    ai: AIAdvisor = Depends(get_ai),
    db: AsyncSession = Depends(get_db),
):
    context = ""
    if data.context_type == "finance":
        try:
            summary = await get_monthly_summary(db)
            context = _finance_context(summary)
        except Exception:
            pass
    elif data.context_type == "workout":
        try:
            history = await get_workout_history(db, limit=5)
            context = _workout_context(history)
        except Exception:
            pass

    response = await ai.ask(question=data.question, context=context, mode=data.mode)
    return {"response": response}


@router.get("/analysis")
async def analysis(
    type: str = "finance",
    user: dict = Depends(get_current_user),
    ai: AIAdvisor = Depends(get_ai),
    db: AsyncSession = Depends(get_db),
):
    if type == "finance":
        summary = await get_monthly_summary(db)
        context = _finance_context(summary)
        response = await ai.ask(
            question="Проанализируй мои финансы за этот месяц. Дай краткие рекомендации.",
            context=context,
            mode="default",
            use_reasoner=True,
        )
        return {"response": response, "summary": summary}
    return {"response": "Тип анализа не поддерживается"}


def _finance_context(summary: dict) -> str:
    lines = [
        f"Доходы: {summary['total_income']:.2f} BYN",
        f"Расходы: {summary['total_expense']:.2f} BYN",
        f"Баланс: {summary['balance']:.2f} BYN\nСчета:",
    ]
    for acc in summary.get("accounts", []):
        lines.append(f"  {acc['name']}: {acc['current']:.2f} {acc.get('currency', 'BYN')}")
    lines.append("Категории расходов:")
    for cat in summary.get("categories", []):
        if cat["type"] == "Расход" and cat["spent"] > 0:
            budget_str = f" / {cat['budget']:.0f}" if cat["budget"] > 0 else ""
            lines.append(f"  {cat['name']}: {cat['spent']:.2f}{budget_str}")
    return "\n".join(lines)


def _workout_context(history: list) -> str:
    lines = ["Последние тренировки:"]
    for w in history[:5]:
        lines.append(
            f"  {w.get('date', '?')} — день {w.get('day_type', '?')}, "
            f"энергия {w.get('energy_before', '?')}/{w.get('energy_after', '?')}"
        )
    return "\n".join(lines)
