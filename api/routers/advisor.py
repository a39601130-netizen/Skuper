"""API роутер: AI советник (PostgreSQL контекст)."""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_ai
from db.database import get_db
from db.services.finance import get_monthly_summary
from db.services.workout import get_workout_history
from services.ai_advisor import AIAdvisor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/advisor", tags=["advisor"])


class HistoryMessage(BaseModel):
    role: str
    text: str


class AskRequest(BaseModel):
    question: str
    mode: str = "default"
    context_type: str = "finance"
    screen_context: Optional[str] = None
    history: Optional[List[HistoryMessage]] = None


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
            logger.exception("Failed to load finance context for advisor")
    elif data.context_type == "workout":
        try:
            history = await get_workout_history(db, limit=5)
            context = _workout_context(history)
        except Exception:
            logger.exception("Failed to load workout context for advisor")

    if data.screen_context:
        sanitized_ctx = data.screen_context[:200].replace('\n', ' ').replace('\r', '')
        context += f"\n\nТекущий экран пользователя: {sanitized_ctx}"

    if data.history:
        context += "\n\nИстория диалога:\n"
        for msg in data.history[-10:]:
            role = "Пользователь" if msg.role == "user" else "AI"
            context += f"{role}: {msg.text}\n"

    try:
        response = await ai.ask(question=data.question, context=context, mode=data.mode)
        return {"response": response}
    except Exception as e:
        logger.error(f"AI advisor error: {e}")
        raise HTTPException(status_code=503, detail="AI сервис временно недоступен")


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
        try:
            response = await ai.ask(
                question="Проанализируй мои финансы за этот месяц. Дай краткие рекомендации.",
                context=context,
                mode="default",
                use_reasoner=True,
            )
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            response = "Не удалось получить анализ от AI"
        return {"response": response, "summary": summary}
    return {"response": "Тип анализа не поддерживается"}


@router.get("/insights")
async def insights(
    user: dict = Depends(get_current_user),
    ai: AIAdvisor = Depends(get_ai),
    db: AsyncSession = Depends(get_db),
):
    try:
        summary = await get_monthly_summary(db)
        context = _finance_context(summary)
        response = await ai.ask(
            question="Дай 2-3 коротких инсайта о моих финансах. Сравни с типичными паттернами. "
                     "Укажи аномалии если есть. Каждый инсайт — одно предложение. "
                     "Ответ в формате JSON массива строк: [\"инсайт1\", \"инсайт2\"]",
            context=context,
            mode="default",
        )
        import json
        try:
            insights_list = json.loads(response)
            if isinstance(insights_list, list):
                return {"insights": insights_list}
        except (json.JSONDecodeError, TypeError):
            pass
        return {"insights": [response]}
    except Exception as e:
        logger.error(f"AI insights error: {e}")
        return {"insights": ["Не удалось получить инсайты"]}


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
