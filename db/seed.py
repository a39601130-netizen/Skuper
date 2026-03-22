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
    {"name": "Повторное знакомство", "weeks": "1-2", "rpe_min": 5, "rpe_max": 6, "sets_modifier": 0.6, "sort_order": 1},
    {"name": "Построение базы",  "weeks": "3-4", "rpe_min": 6, "rpe_max": 7, "sets_modifier": 1.0, "sort_order": 2},
    {"name": "Развитие",         "weeks": "5-8", "rpe_min": 7, "rpe_max": 8, "sets_modifier": 1.0, "sort_order": 3},
    {"name": "Разгрузка",        "weeks": "9",   "rpe_min": 6, "rpe_max": 7, "sets_modifier": 0.5, "sort_order": 4},
]


INITIAL_EXERCISES = [
    # День A — Горизонтальный акцент (Становая + Жим + Горизонтальная тяга)
    {"exercise_id": "deadlift", "name": "Становая тяга", "day": "A", "order": 1,
     "category": "Спина", "weight_step": 2.5, "reps_min": 5, "reps_max": 8, "rest_seconds": 150, "default_sets": 3,
     "notes": "Гриф вдоль тела. Нейтральная спина. Оттолкни пол ногами."},
    {"exercise_id": "bench_press", "name": "Жим лёжа", "day": "A", "order": 2,
     "category": "Грудь", "weight_step": 2.5, "reps_min": 6, "reps_max": 8, "rest_seconds": 150, "default_sets": 4,
     "notes": "Лопатки сведены и опущены. Локти ~45°. Гриф касается груди без отбива."},
    {"exercise_id": "seated_cable_row", "name": "Тяга блока к поясу", "day": "A", "order": 3,
     "category": "Спина", "weight_step": 2.5, "reps_min": 10, "reps_max": 12, "rest_seconds": 90, "default_sets": 3,
     "notes": "Тяни локти к карманам. Сведи лопатки. Контролируй негатив 2-3 сек."},
    {"exercise_id": "rdl_db", "name": "Румынская тяга (гантели)", "day": "A", "order": 4,
     "category": "Ноги", "weight_step": 2.0, "reps_min": 10, "reps_max": 12, "rest_seconds": 90, "default_sets": 2,
     "notes": "Колени слегка согнуты и зафиксированы. Таз назад. Спина нейтральная."},
    {"exercise_id": "face_pull", "name": "Фейс-пулл", "day": "A", "order": 5,
     "category": "Плечи", "weight_step": 1.0, "reps_min": 15, "reps_max": 20, "rest_seconds": 60, "default_sets": 2,
     "notes": "Для здоровья плеч — не гонись за весом. Финиш: поза 'двойной бицепс'."},
    {"exercise_id": "tricep_pushdown", "name": "Разгибание на трицепс", "day": "A", "order": 6,
     "category": "Руки", "weight_step": 1.0, "reps_min": 12, "reps_max": 15, "rest_seconds": 60, "default_sets": 2,
     "notes": "Локти прижаты к корпусу. Полное разгибание внизу."},
    # День B — Вертикальный акцент (Ягодицы + Жим над головой + Вертикальная тяга)
    {"exercise_id": "hip_thrust", "name": "Ягодичный мост (штанга)", "day": "B", "order": 1,
     "category": "Ноги", "weight_step": 2.5, "reps_min": 8, "reps_max": 12, "rest_seconds": 120, "default_sets": 3,
     "notes": "Подбородок к груди. Пауза 1-2 сек вверху. Давление через пятки."},
    {"exercise_id": "ohp", "name": "Жим над головой", "day": "B", "order": 2,
     "category": "Плечи", "weight_step": 2.5, "reps_min": 6, "reps_max": 8, "rest_seconds": 120, "default_sets": 3,
     "notes": "Кор и ягодицы напряжены. Не отклоняй корпус назад. Гриф вверх, не вперёд."},
    {"exercise_id": "lat_pulldown", "name": "Тяга верхнего блока", "day": "B", "order": 3,
     "category": "Спина", "weight_step": 2.5, "reps_min": 8, "reps_max": 10, "rest_seconds": 90, "default_sets": 3,
     "notes": "Тяни к верхней части груди. Полная амплитуда. Контролируй негатив."},
    {"exercise_id": "leg_press", "name": "Жим ногами", "day": "B", "order": 4,
     "category": "Ноги", "weight_step": 5.0, "reps_min": 12, "reps_max": 15, "rest_seconds": 90, "default_sets": 2,
     "notes": "Поясница прижата к спинке ВСЕГДА. Не разгибай колени до конца."},
    {"exercise_id": "lateral_raise", "name": "Разведение гантелей в стороны", "day": "B", "order": 5,
     "category": "Плечи", "weight_step": 1.0, "reps_min": 12, "reps_max": 15, "rest_seconds": 60, "default_sets": 2,
     "notes": "Веди локтями. Не выше плеч. Мизинцы чуть выше больших пальцев."},
    {"exercise_id": "bicep_curl", "name": "Сгибание на бицепс (гантели)", "day": "B", "order": 6,
     "category": "Руки", "weight_step": 1.0, "reps_min": 12, "reps_max": 15, "rest_seconds": 60, "default_sets": 2,
     "notes": "Локти прижаты и неподвижны. Полная амплитуда. Негатив 2-3 сек."},
]


async def seed_db():
    """Seed all initial data if tables are empty."""
    async with async_session() as session:
        await _seed_accounts(session)
        await _seed_categories(session)
        await _seed_phases(session)
        await _seed_exercises(session)
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


async def _seed_exercises(session: AsyncSession):
    result = await session.execute(select(Exercise).limit(1))
    if result.scalar_one_or_none():
        return
    for data in INITIAL_EXERCISES:
        session.add(Exercise(**data))
    # Начальные веса
    for data in INITIAL_EXERCISES:
        cw = CurrentWeight(
            exercise_id=data["exercise_id"],
            weight=0.0,
            target_reps=f"{data['reps_min']}-{data['reps_max']}",
            status="in_progress",
        )
        session.add(cw)
    logger.info(f"Seeded {len(INITIAL_EXERCISES)} exercises with current weights")
