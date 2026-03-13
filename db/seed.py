"""Seed initial data: accounts, categories, exercises, phases."""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import async_session
from db.models import Account, Category, Exercise, Phase, CurrentWeight
import config

logger = logging.getLogger(__name__)


INITIAL_ACCOUNTS = [
    {"name": "Наличные",    "currency": "BYN", "emoji": "💵", "sort_order": 1},
    {"name": "Карта",       "currency": "BYN", "emoji": "🔴", "sort_order": 2},
    {"name": "На Аренду",   "currency": "BYN", "emoji": "🏠", "sort_order": 3},
    {"name": "USD",         "currency": "USD", "emoji": "🇺🇸", "sort_order": 4},
    {"name": "EUR",         "currency": "EUR", "emoji": "🇪🇺", "sort_order": 5},
]

INITIAL_CATEGORIES = [
    # Расходы
    {"name": "Продукты",           "type": "Расход", "budget_limit": 0, "sort_order": 1},
    {"name": "Кафе",               "type": "Расход", "budget_limit": 0, "sort_order": 2},
    {"name": "Транспорт",          "type": "Расход", "budget_limit": 0, "sort_order": 3},
    {"name": "Такси",              "type": "Расход", "budget_limit": 0, "sort_order": 4},
    {"name": "Досуг",              "type": "Расход", "budget_limit": 0, "sort_order": 5},
    {"name": "Покупки",            "type": "Расход", "budget_limit": 0, "sort_order": 6},
    {"name": "Здоровье и красота", "type": "Расход", "budget_limit": 0, "sort_order": 7},
    {"name": "Аптека",             "type": "Расход", "budget_limit": 0, "sort_order": 8},
    {"name": "Ништяки",            "type": "Расход", "budget_limit": 0, "sort_order": 9},
    {"name": "Аренда",             "type": "Расход", "budget_limit": 0, "sort_order": 10},
    {"name": "Коммуналка",         "type": "Расход", "budget_limit": 0, "sort_order": 11},
    {"name": "Интернет и связь",   "type": "Расход", "budget_limit": 0, "sort_order": 12},
    {"name": "Кошки",              "type": "Расход", "budget_limit": 0, "sort_order": 13},
    {"name": "Долги",              "type": "Расход", "budget_limit": 0, "sort_order": 14},
    {"name": "Одежда",             "type": "Расход", "budget_limit": 0, "sort_order": 15},
    {"name": "Подарки",            "type": "Расход", "budget_limit": 0, "sort_order": 16},
    {"name": "Другое",             "type": "Расход", "budget_limit": 0, "sort_order": 17},
    # Доходы
    {"name": "Зарплата",    "type": "Доход", "budget_limit": 0, "sort_order": 1},
    {"name": "Чаевые",      "type": "Доход", "budget_limit": 0, "sort_order": 2},
    {"name": "Подработка",  "type": "Доход", "budget_limit": 0, "sort_order": 3},
    {"name": "Другое",      "type": "Доход", "budget_limit": 0, "sort_order": 4},
]

INITIAL_PHASES = [
    {"name": "Знакомство",       "weeks": "1-2", "rpe_min": 5, "rpe_max": 6, "sets_modifier": 0.5, "sort_order": 1},
    {"name": "Построение базы",  "weeks": "3-4", "rpe_min": 6, "rpe_max": 7, "sets_modifier": 1.0, "sort_order": 2},
    {"name": "Развитие",         "weeks": "5-8", "rpe_min": 7, "rpe_max": 8, "sets_modifier": 1.0, "sort_order": 3},
    {"name": "Разгрузка",        "weeks": "9",   "rpe_min": 6, "rpe_max": 7, "sets_modifier": 0.5, "sort_order": 4},
]


async def seed_db():
    """Seed all initial data if tables are empty."""
    async with async_session() as session:
        await _seed_accounts(session)
        await _seed_categories(session)
        await _seed_phases(session)
        await session.commit()
    logger.info("✅ Database seeded")


async def _seed_accounts(session: AsyncSession):
    result = await session.execute(select(Account).limit(1))
    if result.scalar_one_or_none():
        return
    for data in INITIAL_ACCOUNTS:
        data["emoji"] = config.CATEGORY_EMOJI.get(data["name"], data.get("emoji", "💳"))
        session.add(Account(**data))
    logger.info(f"Seeded {len(INITIAL_ACCOUNTS)} accounts")


async def _seed_categories(session: AsyncSession):
    result = await session.execute(select(Category).limit(1))
    if result.scalar_one_or_none():
        return
    for data in INITIAL_CATEGORIES:
        data["emoji"] = config.CATEGORY_EMOJI.get(data["name"], "📦")
        session.add(Category(**data))
    logger.info(f"Seeded {len(INITIAL_CATEGORIES)} categories")


async def _seed_phases(session: AsyncSession):
    result = await session.execute(select(Phase).limit(1))
    if result.scalar_one_or_none():
        return
    for data in INITIAL_PHASES:
        session.add(Phase(**data))
    logger.info(f"Seeded {len(INITIAL_PHASES)} phases")
